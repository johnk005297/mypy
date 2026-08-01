HELP_TEXT = """
License
    check lic                           check license
    get sid                             get serverId
    apply lic                           apply new license
      optional: [-f path_to_file]
      example:
      apply lic -f /tmp/license.lic
    delete lic                          delete active license
    activate lic                        activate already uploaded license

Transfer data
    export om                           export object model
    import om                           import object model
    export workflows                    export workflows massively
    import workflows                    import workflows
    ls workflows                        display workflows(name: id)
    rm workflows                        delete workflows
    rm files                            clean bim_utils transfer files

User
    ptoken                              get private token
    token                               get user access token(Bearer)
    basic-auth --set                    set basic authentication

Feature Toggle
    ft --list                           display list of features
    optional: [--enabled/--disabled]    display only enabled/disabled FT
    ft [ft_name] [--on/--off]           turn on/off features
    example:
    ft Spatium Bim2d Importbcf --on

ABAC
    abac import                         import attribute-based access control file(s)
    abac export                         export attribute-based access control file(s)

Asset Performance
    asset -h                            perform operations with Asset Performance mgmt

Activity collector
    ac export                           export activity collector configuration file
    ac import -f [path_to_file]         import activity collector configuration file

Custom UI
    apply UI -f [filename]              apply custom user interface

Recalculate paths                       perform methods that recalculates
                                        paths for technical objects
    recalc-paths

Templates
    ls templates                        get list of tempaltes
    export templates --id "id1 id2 ..." export template(s) using id
    risk-ass -f <file>                  import risk assessment template

    m                                   print this menu
    q                                   exit
"""