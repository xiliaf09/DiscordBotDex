-- Script SQL pour corriger la structure de la base de données PostgreSQL
-- Exécutez ce script directement sur votre base de données de production

-- Supprimer l'ancienne table active_snipes si elle existe
DROP TABLE IF EXISTS active_snipes CASCADE;

-- Créer la table tracked_addresses si elle n'existe pas
CREATE TABLE IF NOT EXISTS tracked_addresses (
    address VARCHAR(42) PRIMARY KEY,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer la nouvelle table active_snipes avec la bonne structure
CREATE TABLE active_snipes (
    id SERIAL PRIMARY KEY,
    tracked_address VARCHAR(42) NOT NULL,
    snipe_amount_eth DECIMAL(18,8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
);

-- Vérifier la structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'active_snipes'
ORDER BY ordinal_position;

-- Tester l'insertion d'une adresse trackée
INSERT INTO tracked_addresses (address) VALUES ('0x38B3890A0C0983bE825E353b809A96aC4fA0077e') 
ON CONFLICT (address) DO NOTHING;

-- Tester l'insertion d'un snipe
INSERT INTO active_snipes (tracked_address, snipe_amount_eth, is_active) 
VALUES ('0x38B3890A0C0983bE825E353b809A96aC4fA0077e', 0.001, TRUE);

-- Vérifier les données
SELECT * FROM tracked_addresses WHERE address = '0x38B3890A0C0983bE825E353b809A96aC4fA0077e';
SELECT * FROM active_snipes WHERE tracked_address = '0x38B3890A0C0983bE825E353b809A96aC4fA0077e';
