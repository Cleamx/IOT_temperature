import os
import json
import time
import paho.mqtt.client as mqtt
import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'temperature/#')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'iot_data')
DB_USER = os.getenv('DB_USER', 'iot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'iot_password')


def create_database_connection():
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Connexion à la base de données établie")
            return conn
        except psycopg2.OperationalError as e:
            logger.warning(
                f"Tentative {attempt + 1}/{max_retries} échouée: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Impossible de se connecter à la base de données")
                raise


def init_database(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temperature_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temperature FLOAT,
            humidity FLOAT,
            evapo FLOAT,
            topic VARCHAR(255),
            raw_data JSONB
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp
        ON temperature_data(timestamp DESC)
    """)

    conn.commit()
    cursor.close()
    logger.info("Base de données initialisée")


def insert_data(conn, topic, payload):
    cursor = conn.cursor()

    try:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning(f"Payload non-JSON reçu: {payload}")
            data = {"raw_value": payload}

        temperature = data.get('temperature', data.get('temp'))
        humidity = data.get('humidity', data.get('hum'))
        evapo = data.get('evapo', data.get('VPD'))

        cursor.execute("""
            INSERT INTO temperature_data
            (temperature, humidity, evapo, topic, raw_data)
            VALUES (%s, %s, %s, %s, %s)
        """, (temperature, humidity, evapo, topic, json.dumps(data)))

        conn.commit()
        logger.info(
            f"Données insérées: \n"
            f"temp={temperature}, hum={humidity}, evapo={evapo}")

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion: {e}")
        conn.rollback()
    finally:
        cursor.close()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connecté au broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Abonné au topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Échec de connexion au broker MQTT, code: {rc}")


def on_message(client, userdata, msg):
    logger.info(
        f"Message reçu - Topic: {msg.topic}, Payload: {msg.payload.decode()}")

    db_conn = userdata.get('db_conn')
    if db_conn:
        insert_data(db_conn, msg.topic, msg.payload.decode())


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"Déconnexion inattendue du broker MQTT, code: {rc}")
        logger.info("Tentative de reconnexion...")
        try:
            client.reconnect()
            logger.info("Reconnexion réussie")
        except Exception as e:
            logger.error(f"Échec de reconnexion: {e}")


def main():
    logger.info("Démarrage du service MQTT to Database")

    db_conn = create_database_connection()
    init_database(db_conn)

    client = mqtt.Client(userdata={'db_conn': db_conn})
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.reconnect_delay_set(min_delay=1, max_delay=120)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        logger.error(f"Erreur de connexion au broker MQTT: {e}")
        return

    try:
        client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        logger.info("Arrêt du service...")
    finally:
        client.disconnect()
        db_conn.close()
        logger.info("Service arrêté")


if __name__ == "__main__":
    main()
