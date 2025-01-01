from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

def test_connection():
    try:
        cloud_config = {'secure_connect_bundle': 'secure-connect-cassandra-db.zip'}
        auth_provider = PlainTextAuthProvider('hbhfmkOZekcgsQIWbkrYPwvq', 'aZ4UZiDtNfA_tHdZ1eMem2_aw3LUUo71oADWlhqTTA3vi,wu8wZDjI0aQ0.Nj0emJh-8m+6mLu37GW8R3s8y_KrvUhUuev,2PlZ61F2fGU2IGiM.-obFQyoQhx+LT78d')
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        print("Connection successful!")
    except Exception as e:
        print(f"Error: {e}")

test_connection()
