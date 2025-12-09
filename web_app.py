import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration Base de données
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'iot_data')
DB_USER = os.getenv('DB_USER', 'iot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'iot_password')


def get_db_connection():
    """Crée une connexion à la base de données"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


@app.route('/')
def index():
    """Page principale avec le tableau de données"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API pour récupérer les données"""
    try:
        limit = int(request.args.get('limit', 100))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, temperature, humidity, evapo, topic
            FROM temperature_data
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))
        
        data = cursor.fetchall()
        
        # Convertir les datetime en string pour JSON
        for row in data:
            if row['timestamp']:
                row['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """API pour récupérer les statistiques"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(humidity) as avg_humidity,
                AVG(evapo) as avg_evapo,
                MAX(timestamp) as last_update
            FROM temperature_data
        """)
        
        stats = cursor.fetchone()
        
        if stats['last_update']:
            stats['last_update'] = stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
