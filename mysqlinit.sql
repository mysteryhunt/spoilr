-- totally wipe out spoilr database
DROP DATABASE spoilr;
CREATE DATABASE spoilr;
GRANT ALL PRIVILEGES ON spoilr.* to spoilr @'localhost' IDENTIFIED BY 'spoilr';
FLUSH PRIVILEGES;

