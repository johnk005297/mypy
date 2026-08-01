import typer

import sys
from getpass import getpass

from .auth import Auth
from .license import License, Issue
from bimutils.common import utils


#auth_app CLI
auth_app = typer.Typer(help="Options related to authorization.")

@auth_app.command(name="token")
def get_token(
    url: str = typer.Option(..., "--url", help="URL of the stand which access token is required."),
    providerId: str = typer.Option("", "-pid", "--providerId", help="Bimeister provider Id in cases where more the one providers had been set up."),
    user: str = typer.Option("admin", "-u", "--user", help="Username with access to Bimeister."),
    password: str = typer.Option("Qwerty12345!", "-p", "--password", help="User\'s password with access to Bimeister.")
        ):
    """ Get user access token for a given URL. """

    if not url.startswith('http'):
        url = 'https://' + url
    url = url[:-len('/products')] if url.endswith('/products') else url
    url = url[:-len('/auth')] if url.endswith('/auth') else url
    
    auth = Auth()
    providers = auth.get_providerId(url, interactive=False)
    if providers and isinstance(providers, list) and len(providers) > 1 and not providerId:
        print("Provide needed id with flag -pid / --providerId")
        for provider in providers:
            for k,v in provider.items():
                print(k,v)
    elif providers and providerId:
        token = auth.get_user_access_token(url, user, password, providerId)
        print(token if token else '')
    elif providers and isinstance(providers, str):
        token = auth.get_user_access_token(url, user, password, providers)
        print(token if token else '')


# lic_app CLI
lic_app = typer.Typer(help="Different operations with licenses.")

class LicContext:
    """Store shared license parameters"""
    def __init__(self):
        self.utils = utils
        self.issue = Issue()
        self.auth_ = Auth()
        self.lic = License()

# Create a context instance
lic_context = LicContext()

@lic_app.callback()
def check_connection():
    if not lic_context.utils.is_socket_available(lic_context.issue._license_server, lic_context.issue._license_server_port):
        print(f"License server socket is NOT available <{lic_context.issue._license_server}:{lic_context.issue._license_server_port}>")
        raise typer.Abort()

@lic_app.command(name="issue", help="Issue, apply license.")
def issue_lic(
    version: int = typer.Option(1, "-v", "--version", help="Parameter of the license: version."),
    product: str = typer.Option("Bimeister", "-pr", "--product", help="Parameter of the license: product."),
    licenceType: str = typer.Option("Trial", "-ltype", "--licenceType", help="Parameter of the license: licenceType."),
    activationType: str = typer.Option("Offline", "-atype", "--activationType", help="Parameter of the license: activationType."),
    client: str = typer.Option("", "-c", "--client", help="Parameter of the license: client."),
    clientEmail: str = typer.Option("", "-email", "--clientEmail", help="Parameter of the license: clientEmail."),
    organization: str = typer.Option("", "-org", "--organization", help="Parameter of the license: organization."),
    isOrganization: bool = typer.Option("False", "-isOrg", "--isOrganization", help="Parameter of the license: isOrganization."),
    numberOfUsers: int = typer.Option(50, "-nou", "--numberOfUsers", help="Parameter of the license: numberOfUsers."),
    numberOfIpConnectionsPerUser: int = typer.Option(0, "-uip", "--numberOfIpConnectionsPerUser", help="Parameter of the license: numberOfIpConnectionsPerUser."),
    serverId: str = typer.Option("", "-sid", "--serverId", help="Parameter of the license: serverID. Server which requires a license."),
    period: int = typer.Option(3, "-p", "--period", help="eriod of the license in months."),
    until: str = typer.Option("", "--until", help="Date until the license is valid in format YYYY-MM-DD e.g. 2025-12-26"),
    orderId: str = typer.Option("", "-oId", "--orderId", help="Parameter of the license: orderId."),
    crmOrderId: str = typer.Option("", "-crmId", "--crmOrderId", help="Parameter of the license: crmOrderId."),
    save: bool = typer.Option("False", "-s", "--save", help="Save license into a file."),
    url: str = typer.Option("", "--url", help="URL endpoint which needs a license to activate."),
    print_: bool = typer.Option("False", "--print", help="Print license on a screen."),
    user: str = typer.Option("admin", "-u", "--user", help="Username with access to web interface and privileges to work with licenses."),
    password: str = typer.Option("Qwerty12345!", "-pw", "--password", help="User's password to web interface."),
    apply: bool = typer.Option("False", "--apply", help="Activate license for specified URL. Requires --url flag.")
            ):
    if url and serverId:
        typer.echo("Error: Cannot use --url and --serverId together.")
        raise typer.Abort()
    elif not serverId and not url:
        typer.echo("Error: Either --serverId or --url is required.")
        raise typer.Abort()
    lic_username, lic_password = lic_context.utils.get_creds_from_env('LICENSE_USER', 'LICENSE_PASSWORD')
    if not lic_username or not lic_password:
        print("Enter credentials for license server:")
        lic_username = input("login: ")
        lic_password = getpass("password: ")
    token = lic_context.issue.get_token_to_issue_license(username=lic_username, password=lic_password)
    if not token:
        sys.exit()
    params = locals().copy()
    if serverId:
        server_license = lic_context.issue.issue_license(**params)
    else:
        url = url[:-1] if url.endswith('/') else url
        url = url[:-len("/auth")] if url.endswith('/auth') else url
        url = url[:-len("/products")] if url.endswith('/products') else url
        url = "https://" + url if not url.startswith('http') else url
        if not lic_context.utils.is_url_available(url):
            print(f"URL: {url} is not available.")
            raise typer.Abort()
        check = lic_context.auth_.establish_connection(url=url, username=user, password=password)
        if not check:
            sys.exit()
        success, message = lic_context.lic.get_serverID(url, lic_context.auth_.token)
        if success:
            params['serverId'] = message
        else:
            print(f"Error: {message}")
        server_license = lic_context.issue.issue_license(**params)
        if apply:
            lic_context.lic.apply_license(url, lic_context.auth_.token, user, password, raw_data=server_license)