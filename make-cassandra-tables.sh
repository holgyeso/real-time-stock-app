CQL="
CREATE KEYSPACE stockapp WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
CREATE TABLE IF NOT EXISTS stockapp.trades(ts timestamp, symbol VARCHAR, price DECIMAL, volume INT, PRIMARY KEY(symbol, ts));
"

until echo $CQL | cqlsh; do
  echo "cqlsh: Cassandra is unavailable to initialize - will retry later"
  sleep 2
done &

exec /usr/local/bin/docker-entrypoint.sh "$@"