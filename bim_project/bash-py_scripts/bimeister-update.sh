#!/bin/bash

set -eo pipefail

__VERSION__="0.0.20"


print_help() {
  cat <<EOF
  Скрипт для обновления ППО Bimeister.
  Аргументы:
    Обязательные:
    --env               - контур, где выполняется обновление(test, prod, demo)
    -b, --build         - имя каталога со сборкой bimeister(152_1.18.0-shae3ba5ce4, 152-patch_1.18.0-shae3ba5ce4)

    Опциональные:
    -lu, --local-update     - директива для указания, что обновляются внутренние стенды bimeister
    --create-db             - директива для указания того, что требуется создание новых БД и их пользователей
    -spc, --skip-pods-check - директива для указания того, что требуется пропустить проверку статусов подов k8s
    --skip-images           - директива для указания того, что требуется пропустить шаг прогрузки образов
    --push-images           - директива для указания того, что требуется обязательная прогрузка образов
    -sfc, --skip-ft-check   - директива для указания того, что требуется пропустить шаг проверки feature toggle
                              между исходными данными в confluence и стендом

  Примеры запуска:
    $ bash bimeister-update.sh --env test --build 152_1.18.0-shae3ba5ce4
    $ bash bimeister-update.sh --env prod -b 152_1.18.0-shae3ba5ce4 --create-db
    $ bash bimeister-update.sh --env demo -b 152-patch_1.18.0-shae3ba5ce4 --create-db --local-update
EOF
  exit
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --env) shift; ENV=${1,,};; # convert argument to lowercase
      --build|-b) shift; BUILD_FOLDER=${1};;
      --local-update|-lu) IS_LOCAL_UPDATE=true;;
      --create-db) IS_NEW_DB=true;;
      --skip-images) SKIP_IMAGES=true;;
      --push-images) PUSH_IMAGES=true;;
      --skip-pods-check|-spc) SKIP_PODS_CHECK=true;;
      --skip-ft-check|-sfc) SKIP_FT_CHECK=true;;
      --help|-h) print_help;;
      *) echo "Illegal argument ${1}"; print_help;;
    esac
    shift
  done
}

check_required_apps() {
  # Function to check for all necessary components

  local REQUIRED_APPS=(
      skopeo
      jq
      yq
      kubectl
      helm
      ansible-playbook
      k9s
      curl
  )
  for APP in ${REQUIRED_APPS[@]};do
    if ! which ${APP} > /dev/null 2>&1; then
      echo "Requirements check: FAILED."
      echo
      echo "$APP not found!"
      echo "Install $APP before run script: sudo dnf install -y $APP"
      exit 1
    fi
  done
  echo "Requirements check: OK."
}

check_kubeAPI_connection() {
  if ! kubectl cluster-info > /dev/null 2>&1; then
      echo "K8S API connection check: FAILED."
      echo
      echo "Kubernetes API is not available. User: $(whoami)"
      exit 1
  else
    echo "K8S API connection check: OK."
  fi
}

check_pods_status() {
  # Check if all pods in the namespace are Running or Completed

  if [[ "$SKIP_PODS_CHECK" == "true" ]]; then
    echo "K8S PODs status check: skipped."
    return 0
  fi
  local FILTER='.items[] | select(
    (.status.phase != "Running" and .status.phase != "Succeeded") or
    (.status.phase == "Running" and any(.status.containerStatuses[]; .ready == false))
    )'
  local FAILED_PODS_COUNT=$(kubectl get pods -n "$NAMESPACE" -o json | jq "[${FILTER}] | length")
  if [ "${FAILED_PODS_COUNT}" -eq 0 ]; then
    echo "K8S PODs status check: OK."
  else
    echo "K8S PODs status check: FAILED."
    echo
    echo "Check pods:"
    kubectl get pods -n "$NAMESPACE" -o json | jq -r "${FILTER} | .metadata.name" \
      | while read -r pod; do echo "- $pod"; done
      exit 1
  fi
}

is_path_exists() {
  # Function checks if file/directory exists.
  # Expects two arguments: full path to check(mandatory) and a print message(optional).
  local PATH_TO_CHECK=$1
  local FAILED_MSG=${2:-"Path check: FAILED."}
  local SUCCESS_MSG=${3:-""}
  if [ ! -e "$PATH_TO_CHECK" ]; then
    [[ -n "$FAILED_MSG" ]] && echo "$FAILED_MSG"
    echo
    echo "Error. Path not found: $PATH_TO_CHECK"
    exit 1
  fi
  [[ -n "$SUCCESS_MSG" ]] && echo "$SUCCESS_MSG"
  return 0
}

remove_matviews() {
  # Function expects db hostname as an argument.
  # Stop reportscollector and remove matviews.
  # So far function is only necessary for Suid project.

  echo -n "Pause reportscollector cronjob: "
  kubectl patch cronjobs -n bimeister reportscollector -p '{"spec": {"suspend": true}}'
  local DB_PORT=$(yq '.bimeister_db_port' ${ENV_FILE_PATH})
  local DB_USERNAME=$(yq '.bimeister_databases.bimeisterdb.username' ${ENV_FILE_PATH})
  local DB_PASSWORD=$(yq '.bimeister_databases.bimeisterdb.password' ${ENV_FILE_PATH})
  echo -n "Matviews "
  bimutils sql -s $1 -p ${DB_PORT} -d bimeisterdb -u ${DB_USERNAME} -pw ${DB_PASSWORD} --drop-matviews sf_*
}

push_images_to_registry() {
  # Push images to registry only during test environment update
  # Some registry may not have username or password.

  local SKIP_MSG="Push images: skipped."
  if $SKIP_IMAGES; then
    echo $SKIP_MSG
    return 0
  fi
  if [[ "${ENV}" == "test" || "${ENV}" == "demo" || "${PUSH_IMAGES}" == "true" ]]; then
    echo "Start pushing images to registry"
    REGISTRY_HOST=$(yq '.registry' ${ENV_FILE_PATH})
    REGISTRY_USER=$(yq '.registry_username' ${ENV_FILE_PATH})
    REGISTRY_PASS=$(yq '.registry_password' ${ENV_FILE_PATH})
    if [[ -z "${REGISTRY_HOST}" ]]; then
          echo "No registry name was found in ${ENV}. Exit!"
          exit 1
    elif [[ -z "${REGISTRY_USER}" || -z "${REGISTRY_PASS}" ]]; then
        skopeo-push-images.sh --ignore-tls -i ${RELEASE_PATH}/tools/images/images.tar -r ${REGISTRY_HOST}
    else
        skopeo-push-images.sh --ignore-tls -i ${RELEASE_PATH}/tools/images/images.tar -r ${REGISTRY_HOST} -u ${REGISTRY_USER} -p ${REGISTRY_PASS}
    fi
  else
    echo $SKIP_MSG
  fi
}

get_db_host() {
  # Function defines database server name/IP and returns it's value.

  local DB_HOST=$(yq '.db1' ${ENV_FILE_PATH})
  if [[ "${ENV}" == "prod" ]]; then
    # need to define patroni's cluster SSL configuration
    local HTTP=""
    if curl -k https://${DB_HOST}:8008/health > /dev/null 2>&1; then
      HTTP="https"
    else
      HTTP="http"
    fi
    DB_HOST=$(curl -s ${HTTP}://${DB_HOST}:8008/cluster | jq '.members[] | select(.role == "leader") | .host' | tr -d '"')
  fi
  echo ${DB_HOST}
}

prepare_venv() {
  local TARGET_VENV_DIR_PATH="/opt/bimeister"
  local SOURCE_VENV_DIR_PATH="${RELEASE_PATH}/tools/box-venv"
  echo "Preparing virtual environment..."
  sudo rsync -a --delete ${SOURCE_VENV_DIR_PATH} ${TARGET_VENV_DIR_PATH}/
  source /opt/bimeister/box-venv/bin/activate
  if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Virtual environment check: FAILED."
    exit 1
  else
    echo "Virtual environment check: OK."
  fi
}

sync_env_files(){
  # Function confirms correct env file structure on the server in /bimeister/releases/.env
  local DEFAULT_PASS=""
  if $IS_LOCAL_UPDATE; then
    DEFAULT_PASS="--default-pass"
  fi
    sync_check=$(sudo python3 ${RELEASE_PATH}/tools/scripts/sync-env-files.py --env ${ENV} --release ${RELEASE} ${DEFAULT_PASS})
  if [[ "${sync_check}" == "OK." ]]; then
    echo "Env file structure check: OK."
  else
    echo "Env file structure check: FAILED."
    echo
    echo "$sync_check"
    exit 1
  fi
}

check_mandatory_arguments() {
  # Function checks if mandatory variables were provided
  local MANDATORY_ARGS=("ENV" "BUILD_FOLDER")
  for ARG in "${MANDATORY_ARGS[@]}"; do
    if [[ -z "${!ARG}" ]]; then
      local ENV="--env"
      local BUILD_FOLDER="--build"
      echo "Error: missing mandatory argument: ${!ARG}"
      echo
      print_help
      exit 1
    fi
  done
}

start_k9s() {
  # Function runs k9s console.
  # Takes an optional argument as a timer to wait before launch.
  local TSECONDS=${1:-0}
  while [ $TSECONDS -gt 0 ]; do
    printf "\rK9S will start in: %d seconds " "$TSECONDS"
    sleep 1
    ((TSECONDS--))
  done
  k9s
}

check_hostname() {
  # Function tries to find 'bimeister.io' part in local hostname.
  # Purpose: small precaution to prevent engineer from forgetting to provide --local-update flag.
  local HOSTNAME=$(hostname -f 2>/dev/null || hostname)
  local PATTERN="bimeister.io"
  if ! $IS_LOCAL_UPDATE && [[ $HOSTNAME == *$PATTERN* ]]; then
    echo "Found $PATTERN in hostname. Forgot --local-update flag?!"
    exit 1
  fi
}

get_ssh_creds() {
  # Function takes username and password in case if SSH access requires
  local -n USER_REF=$1 PASS_REF=$2
  USER_REF=$USER
  [[ $EUID -eq 0 ]] && read -p "Enter SSH username: " USER_REF
  read -sp "Enter SSH password: " PASS_REF
}

get_build_metadata() {
  # Function gets needed data from build.yaml file.
  local -n RELEASE_REF=$1 PROJECT_REF=$2
  local DATA_PATH="${RELEASE_PATH}/build.yaml"
  is_path_exists $DATA_PATH "Metadata file path check: FAILED."
  RELEASE_REF=$(yq '.release_version' $DATA_PATH)
  PROJECT_REF=$(yq '.project_name' $DATA_PATH)
}

check_feature_toggles() {
  # Function checks FT between confluence data and current FT on a stand.

  if [[ "$SKIP_FT_CHECK" == "true" ]] || [[ "$IS_LOCAL_UPDATE" != "true" ]]; then
    echo "Feature toggles check: skipped."
    return 0
  fi
  local CHECK_FT=$(bimutils ft -${__PROJECT__} --env ${ENV} --check)
  if [[ "${CHECK_FT}" == "Total match!" ]]; then
    echo "Feature toggles check: OK."
  else
    echo "Feature toggles check: FAILED."
    echo
    echo "$CHECK_FT"
    exit 1
  fi
}



# THE MAIN LOGIC OF THE SCRIPT STARTS HERE

## BEGIN variables initialization ##
# LOG_FILENAME=$(basename "$0")
# LOG_PATH="${HOME}/${LOG_FILENAME%.*}.log"
# exec 3>&1
# exec &> >(tee "$LOG_PATH")
NAMESPACE="bimeister"
IS_LOCAL_UPDATE=false
IS_NEW_DB=false
SKIP_IMAGES=false
PUSH_IMAGES=false
SKIP_PODS_CHECK=false
SKIP_FT_CHECK=false
parse_args "$@"
RELEASE_PATH="/bimeister/releases/${BUILD_FOLDER}"
ENV_FILE_PATH="/bimeister/releases/.env/${ENV}.yaml"
ANSIBLE_CFG_PATH=${RELEASE_PATH}/tools/ansible.cfg
## END variables initialization ##

## BEGIN preparation checks ##
if ! sudo -n true &> /dev/null; then
  echo "Script requires sudo privileges!" && exit 1
fi
check_hostname
check_mandatory_arguments
get_build_metadata RELEASE __PROJECT__
prepare_venv
check_required_apps
check_kubeAPI_connection
check_pods_status
is_path_exists ${RELEASE_PATH} "Release path check: FAILED." "Release path check: OK."
is_path_exists ${ENV_FILE_PATH} "Env file check: FAILED." "Env file check: OK."
sync_env_files
check_feature_toggles
echo
## END preparation checks ##

## BEGIN prepare upgrade ##
if $IS_NEW_DB; then
  get_ssh_creds SSH_USER SSH_PASS
fi
echo "Creating hosts and values files..."
ANSIBLE_CONFIG=${ANSIBLE_CFG_PATH} \
ansible-playbook ${RELEASE_PATH}/tools/create-hosts-and-values-files.yaml -e "env=${ENV} is_local_update=${IS_LOCAL_UPDATE}"

# create database(s) and user(s) if needed
if $IS_NEW_DB; then
  ANSIBLE_CONFIG=${ANSIBLE_CFG_PATH} \
  ansible-playbook -i ${RELEASE_PATH}/inventory/hosts.yaml ${RELEASE_PATH}/tools/create-databases-and-users.yaml \
  -e "ansible_user=${SSH_USER} ansible_ssh_pass=${SSH_PASS} ansible_become_pass=${SSH_PASS}"
fi

push_images_to_registry

if [[ "${__PROJECT__}" == "suid" ]]; then
  # Stop reportscollector and remove matviews
  DB_HOST=$(get_db_host)
  remove_matviews ${DB_HOST}
fi
## END prepare upgrade ##

## BEGIN upgrade ##
echo "Test upgrade in DRY-RUN mode"
helm upgrade bimeister -n bimeister ${RELEASE_PATH}/helm/charts/bimeister -f ${RELEASE_PATH}/helm/values/bimeister.yaml --dry-run # >&3 2>&3
echo
echo "BEGIN UPGRADE..."
helm upgrade bimeister -n bimeister ${RELEASE_PATH}/helm/charts/bimeister -f ${RELEASE_PATH}/helm/values/bimeister.yaml # >&3 2>&3
echo
echo "UPGRADE FINISHED!"
echo "Необходимо убедиться, что все сервисы пространства bimeister запущены(может занять до 15-ти минут)"
echo
start_k9s 10
echo
## END upgrade ##

## BEGIN post upgrade tasks ##
if [[ "${__PROJECT__}" == "suid" ]]; then
  # Resume reportscollector cronjob
  echo
  echo "После запуска всех сервисов необходимо вручную восстановить работу представлений:"
  echo "kubectl patch cronjobs -n bimeister reportscollector -p '{\"spec\": {\"suspend\": false}}'"
fi
## END post upgrade tasks ##