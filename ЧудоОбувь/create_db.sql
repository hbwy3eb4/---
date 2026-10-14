CREATE TABLE roles(id SERIAL PRIMARY KEY, name VARCHAR(50));
CREATE TABLE users(id SERIAL PRIMARY KEY, last_name VARCHAR(50),
    first_name VARCHAR(50), middle_name VARCHAR(50),
    login VARCHAR(50), role_id INT REFERENCES roles(id));
CREATE TABLE products(id SERIAL PRIMARY KEY, category VARCHAR(50),
    subcategory VARCHAR(50), image_path VARCHAR(100), name VARCHAR(255),
    manufacturer VARCHAR(100), description TEXT, composition TEXT,
    price NUMERIC(10,2));
CREATE TABLE sizes(id SERIAL PRIMARY KEY, value NUMERIC(4,1));
CREATE TABLE stock_items(id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    size_id INT REFERENCES sizes(id), quantity INT);
CREATE TABLE orders(id SERIAL PRIMARY KEY, order_date DATE,
    user_id INT REFERENCES users(id));
CREATE TABLE order_items(id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    size_id INT REFERENCES sizes(id),
    quantity INT, price NUMERIC(10,2));