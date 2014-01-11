-- totally wipe out spoilr database
DROP DATABASE spoilr;
CREATE DATABASE spoilr;
GRANT ALL PRIVILEGES ON spoilr.* to 'spoilr'@'%' IDENTIFIED BY 'spoilr';
GRANT ALL PRIVILEGES ON spoilr.* to 'spoilr'@'localhost' IDENTIFIED BY 'spoilr';
GRANT USAGE ON *.* to 'monitoring'@'%' IDENTIFIED BY 'dup3m3';
GRANT USAGE ON *.* to 'monitoring'@'localhost' IDENTIFIED BY 'dup3m3';
GRANT REPLICATION CLIENT on *.* to 'monitoring'@'%' identified by 'dup3m3';
GRANT REPLICATION CLIENT on *.* to 'monitoring'@'localhost' identified by 'dup3m3';
GRANT SELECT ON *.* to 'monitoring'@'%';
GRANT SELECT ON *.* to 'monitoring'@'localhost';
FLUSH PRIVILEGES;

