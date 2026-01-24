#!/bin/bash

# Script is only applicable on servers with kubeAPI access. 
# It's going to be a part of automation process of cleaning space on the nodes from unused images.

__version__=0.1.0

# check if kubeAPI is available
kubectl get no > /dev/null 2>&1
if [ $? -ne 0 ]; then
	echo "Kube API inaccessible. Exit!"
    exit 1
fi

# check if crictl is available
crictl > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "crictl isn't available. Exit!"
    exit 1
fi

ImagesInUse=($(kubectl get pods --all-namespaces -o jsonpath="{.items[*].spec['initContainers', 'containers'][*].image}" | tr -s '[[:space:]]' '\n' | sort | uniq))
ImagesOnHost=($(crictl image ls | awk 'NR>1 {print $1 ":" $2 "#" $3}'))

removeUnusedImages() {
  for image in "${ImagesOnHost[@]}"
  do
    # split ${image} with # symbol and drop the suffix
    imageNameTag=${image%#*}
    if [[ ${ImagesInUse[@]} =~ ${imageNameTag} ]]
      then
        continue
    elif [[ ${ImagesInUse[@]} =~ ${imageNameTag#*/} ]]
      then
        continue
    elif [[ ${image} =~ 'pause:' ]]
      then
        continue
    else
      # split ${image} with # symbol and drop the prefix
      crictl rmi ${image#*#}
    fi
  done
}

count_images() {
    number_of_images=($(crictl image ls | awk 'NR>1' | wc -l))
    echo ${number_of_images}
}

count_before=$(count_images)
removeUnusedImages
count_after=$(count_images)
result_count=$(( ${count_before} - ${count_after} ))
echo "Removed images: ${result_count}"
echo "Total images: $(count_images)"

