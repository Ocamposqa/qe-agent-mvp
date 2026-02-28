@description('Location for all resources.')
param location string = resourceGroup().location

@description('Environment name prefix.')
param envName string = 'quantumqe'

// 1. Log Analytics Workspace (App Insights Backbone)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${envName}-law'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
  }
}

// 2. Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${envName}-appinsights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// 3. Azure Service Bus (Message Queue for decoupling tests)
resource serviceBus 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: '${envName}-sb'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource testQueue 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = {
  parent: serviceBus
  name: 'mission-queue'
  properties: {
    lockDuration: 'PT5M'
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P14D'
  }
}

// 4. Azure Web PubSub (Real-time telemetry streaming to UI)
resource webPubSub 'Microsoft.SignalRService/webPubSub@2021-10-01' = {
  name: '${envName}-wps'
  location: location
  sku: {
    name: 'Free_F1'
    capacity: 1
  }
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

// 5. Azure Cosmos DB (Agent Memory & Telemetry)
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: '${envName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0, isZoneRedundant: false }]
    capabilities: [{ name: 'EnableServerless' }]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosDb
  name: 'QuantumDB'
  properties: {
    resource: {
      id: 'QuantumDB'
    }
  }
}

// 6. Azure Container Apps Environment
resource acaEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${envName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Outputs to inject into the App configurations
output serviceBusEndpoint string = serviceBus.properties.serviceBusEndpoint
output pubSubEndpoint string = webPubSub.properties.hostName
output appInsightsKey string = appInsights.properties.InstrumentationKey
