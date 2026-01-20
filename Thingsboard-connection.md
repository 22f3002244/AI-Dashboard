# ThingsBoard Python Data Retrieval - Code Reference

## 1. Installation & Setup

```bash
# Install the REST client
pip install tb-rest-client

# Or for specific version
pip install tb-rest-client==1.9.0
```

## 2. Authentication & Connection

### For Community Edition (CE)
```python
from tb_rest_client.rest_client_ce import RestClientCE
from tb_rest_client.rest import ApiException

# ThingsBoard connection details
THINGSBOARD_URL = "http://localhost:8080"  # or your server URL
USERNAME = "tenant@thingsboard.org"         # your username
PASSWORD = "tenant"                          # your password

# Initialize and login
with RestClientCE(base_url=THINGSBOARD_URL) as rest_client:
    try:
        # Login and get token
        rest_client.login(username=USERNAME, password=PASSWORD)
        print("✓ Successfully connected to ThingsBoard")
        
        # Your code here...
        
    except ApiException as e:
        print(f"✗ Authentication failed: {e}")
```

### For Professional Edition (PE)
```python
from tb_rest_client.rest_client_pe import RestClientPE

with RestClientPE(base_url=THINGSBOARD_URL) as rest_client:
    rest_client.login(username=USERNAME, password=PASSWORD)
    # Your code here...
```

## 3. Get Devices

### Get All Devices
```python
# Get all devices (paginated)
devices = rest_client.get_tenant_devices(page_size=1000, page=0)

print(f"Total devices: {devices.total_elements}")

for device in devices.data:
    print(f"Device: {device.name} (ID: {device.id.id})")
    print(f"  Type: {device.type}")
    print(f"  Label: {device.label}")
```

### Get Device by Name
```python
device_name = "Temperature Sensor 01"
device = rest_client.get_tenant_device(device_name)

if device:
    device_id = device.id.id
    print(f"Found device: {device.name} with ID: {device_id}")
```

### Get Device by ID
```python
from tb_rest_client.models.models_ce import DeviceId

device_id = "your-device-id-here"
device_id_obj = DeviceId(device_id)

device_info = rest_client.get_device_by_id(device_id_obj)
print(f"Device Name: {device_info.name}")
```

## 4. Get Latest Telemetry Data

```python
# Get latest telemetry for specific keys
keys = "temperature,humidity,pressure"  # comma-separated keys

latest_telemetry = rest_client.get_latest_timeseries(
    entity_type="DEVICE",
    entity_id=device_id,
    keys=keys
)

# Parse the data
for key, value_list in latest_telemetry.items():
    if value_list:
        latest_value = value_list[0]
        print(f"{key}: {latest_value['value']} (timestamp: {latest_value['ts']})")
```

## 5. Get Historical Telemetry Data

```python
import time

# Define time range
end_ts = int(time.time() * 1000)        # Current time in milliseconds
start_ts = end_ts - (24 * 60 * 60 * 1000)  # 24 hours ago

# Get historical data
historical_data = rest_client.get_timeseries(
    entity_type="DEVICE",
    entity_id=device_id,
    keys=keys,
    start_ts=start_ts,
    end_ts=end_ts,
    interval=3600000,  # 1 hour intervals (in milliseconds)
    limit=1000,
    agg="AVG"  # Aggregation: AVG, MIN, MAX, SUM, COUNT, NONE
)

# Process the data
for key, values in historical_data.items():
    print(f"\n{key}:")
    for record in values:
        timestamp = record['ts']
        value = record['value']
        # Convert timestamp to readable format
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp / 1000)
        print(f"  {dt}: {value}")
```

## 6. Get Device Attributes

```python
# Get all attributes
attributes = rest_client.get_attributes(
    entity_type="DEVICE",
    entity_id=device_id,
    keys=None  # None gets all attributes
)

# Attributes are divided into scopes
print("Client attributes:", attributes.get('CLIENT_SCOPE', {}))
print("Shared attributes:", attributes.get('SHARED_SCOPE', {}))
print("Server attributes:", attributes.get('SERVER_SCOPE', {}))
```

### Get Specific Attribute Keys
```python
# Get specific attributes
attr_keys = "active,location"
attributes = rest_client.get_attributes(
    entity_type="DEVICE",
    entity_id=device_id,
    keys=attr_keys
)
```

## 7. Complete Example: Export Data to CSV

```python
import pandas as pd
from datetime import datetime
from tb_rest_client.rest_client_ce import RestClientCE

THINGSBOARD_URL = "http://localhost:8080"
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"
DEVICE_NAME = "DHT22"

with RestClientCE(base_url=THINGSBOARD_URL) as rest_client:
    # Login
    rest_client.login(username=USERNAME, password=PASSWORD)
    
    # Get device
    device = rest_client.get_tenant_device(DEVICE_NAME)
    device_id = device.id.id
    
    # Get last 7 days of data
    end_ts = int(time.time() * 1000)
    start_ts = end_ts - (7 * 24 * 60 * 60 * 1000)
    
    # Get telemetry
    data = rest_client.get_timeseries(
        entity_type="DEVICE",
        entity_id=device_id,
        keys="temperature,humidity",
        start_ts=start_ts,
        end_ts=end_ts,
        limit=10000
    )
    
    # Convert to DataFrame
    records = []
    for key, values in data.items():
        for record in values:
            records.append({
                'timestamp': datetime.fromtimestamp(record['ts'] / 1000),
                'key': key,
                'value': record['value']
            })
    
    df = pd.DataFrame(records)
    
    # Pivot to wide format
    df_wide = df.pivot(index='timestamp', columns='key', values='value')
    df_wide.reset_index(inplace=True)
    
    # Export to CSV
    df_wide.to_csv('thingsboard_data.csv', index=False)
    print("✓ Data exported to thingsboard_data.csv")
```

## 8. Error Handling Best Practices

```python
from tb_rest_client.rest import ApiException

try:
    rest_client.login(username=USERNAME, password=PASSWORD)
    
    # Your operations
    devices = rest_client.get_tenant_devices(page_size=100, page=0)
    
except ApiException as e:
    if e.status == 401:
        print("Authentication failed - check credentials")
    elif e.status == 404:
        print("Resource not found")
    elif e.status == 429:
        print("Rate limit exceeded")
    else:
        print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 9. Working with Multiple Devices

```python
# Get telemetry from multiple devices
devices = rest_client.get_tenant_devices(page_size=100, page=0)

all_data = {}

for device in devices.data:
    device_id = device.id.id
    device_name = device.name
    
    # Get latest telemetry
    telemetry = rest_client.get_latest_timeseries(
        entity_type="DEVICE",
        entity_id=device_id,
        keys="temperature,humidity"
    )
    
    all_data[device_name] = telemetry
    
# Process all_data dictionary
for device_name, telemetry in all_data.items():
    print(f"\n{device_name}:")
    for key, values in telemetry.items():
        if values:
            print(f"  {key}: {values[0]['value']}")
```

## 10. Key Parameters Reference

### Time Parameters
- `start_ts`: Start timestamp in milliseconds (Unix epoch)
- `end_ts`: End timestamp in milliseconds
- `interval`: Aggregation interval in milliseconds

### Aggregation Types
- `NONE`: Raw data points
- `AVG`: Average values
- `MIN`: Minimum values
- `MAX`: Maximum values
- `SUM`: Sum of values
- `COUNT`: Count of data points

### Entity Types
- `DEVICE`
- `ASSET`
- `ENTITY_VIEW`
- `CUSTOMER`
- `TENANT`
- `DASHBOARD`

### Common Time Conversions
```python
import time
from datetime import datetime, timedelta

# Current time in milliseconds
current_ms = int(time.time() * 1000)

# 1 hour ago
one_hour_ago = current_ms - (60 * 60 * 1000)

# 24 hours ago
one_day_ago = current_ms - (24 * 60 * 60 * 1000)

# 7 days ago
one_week_ago = current_ms - (7 * 24 * 60 * 60 * 1000)

# Specific date to milliseconds
specific_date = datetime(2024, 1, 15, 12, 0, 0)
specific_ms = int(specific_date.timestamp() * 1000)

# Milliseconds to datetime
dt = datetime.fromtimestamp(timestamp_ms / 1000)
```
