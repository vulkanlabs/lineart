-- docker exec -it sketch-app-db-1 bash
-- psql -U $POSTGRES_USER -d $POSTGRES_DB
INSERT INTO users
(user_auth_id, email, name)
VALUES
('00000000-00000-0000-0000-00000000000', 'email@vulkan.software', 'Nome');