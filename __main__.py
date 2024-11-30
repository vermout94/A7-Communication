import pulumi
import pulumi_azure_native
from pulumi_azure_native import network, cognitiveservices, web
from pulumi_azure_native.network import VirtualNetworkLink, SubResourceArgs
import os

# Resource Group
resource_group_name = "wi22b116_rg_1569"

# Virtual Network
vnet = network.VirtualNetwork(
    "app-vnet",
    resource_group_name=resource_group_name,
    location="westeurope",
    address_space=network.AddressSpaceArgs(address_prefixes=["10.0.0.0/16"])
)

# Subnets
web_app_subnet = network.Subnet(
    "web-app-subnet",
    resource_group_name=resource_group_name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24"
)

ai_service_subnet = network.Subnet(
    "ai-service-subnet",
    resource_group_name=resource_group_name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.2.0/24",
    private_endpoint_network_policies="Disabled",
    service_endpoints=[
        network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.CognitiveServices"
        )
    ]
)

# Private DNS Zone
dns_zone = pulumi_azure_native.network.PrivateZone(
    "private-dns-zone",
    resource_group_name=resource_group_name,
    location="Global",
    private_zone_name="privatelink.cognitiveservices.azure.com"
)

dns_link = VirtualNetworkLink(
    "dns-link",
    resource_group_name=resource_group_name,
    private_zone_name=dns_zone.name,
    registration_enabled=True,
    virtual_network=SubResourceArgs(id=vnet.id),
    location="Global"
)

ai_private_endpoint = network.PrivateEndpoint.get(
    "ai-private-endpoint",
    id="/subscriptions/76ec05d1-aea1-4612-a53d-65456bb6faef/resourceGroups/wi22b116_rg_1569/providers/Microsoft.Network/privateEndpoints/ai-private-endpoint388a6f7c"
)


app_service_plan = web.AppServicePlan.get(
    "web-app-plan",
    id="/subscriptions/76ec05d1-aea1-4612-a53d-65456bb6faef/resourceGroups/wi22b116_rg_1569/providers/Microsoft.Web/serverfarms/web-app-planb1af4145"
)

# Reference Existing Web App
web_app = web.WebApp.get(
    "web-app",
    id="/subscriptions/76ec05d1-aea1-4612-a53d-65456bb6faef/resourceGroups/wi22b116_rg_1569/providers/Microsoft.Web/sites/web-app77df4cc8"
)

ai_service = cognitiveservices.Account(
    "ai-service-config",
    resource_group_name="wi22b116_rg_1569",
    account_name="webappaiservice",
    location="westeurope",
    kind="TextAnalytics",
    sku={
        "name": "F0",
    },
    properties=cognitiveservices.AccountPropertiesArgs(
        public_network_access="Disabled",  # Disable public network access
        custom_sub_domain_name="webappaiservice",
        network_acls=cognitiveservices.NetworkRuleSetArgs(  # Configure Network ACLs
            default_action="Deny",  # Deny by default
            virtual_network_rules=[
                cognitiveservices.VirtualNetworkRuleArgs(
                    id=ai_service_subnet.id,  # Associate with the AI service subnet
                )
            ],
            ip_rules=[]  # No specific IP rules if you want full restriction
        ),
    )
)


pulumi.export("vnet_name", vnet.name)
