-- users
CREATE TABLE user_table (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email VARCHAR(255)
);

-- products
CREATE TABLE product_table (
    product_id SERIAL PRIMARY KEY,
    product_name TEXT UNIQUE NOT NULL,
    manual TEXT,
    category VARCHAR
);

-- saved products
CREATE TABLE saved_products (
    user_id INT REFERENCES user_table(user_id),
    product_id INT REFERENCES product_table(product_id),
    PRIMARY KEY (user_id, product_id)
);

-- images
CREATE TABLE image_table (
    image_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES product_table(product_id),
    image_url TEXT NOT NULL
);

-- purchase links
CREATE TABLE purchase_link_table (
    purchase_link_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES product_table(product_id),
    purchase_link TEXT NOT NULL
);