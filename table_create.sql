CREATE TABLE main_products (
    main_product_id VARCHAR(100) PRIMARY KEY,
    name TEXT,
    category TEXT,
    base_url TEXT,
    tag TEXT
);

CREATE TABLE fit_variations (
    unique_fit_id VARCHAR(100) PRIMARY KEY,
    main_product_id VARCHAR(100) REFERENCES main_products(main_product_id),
    fit_product_id TEXT,
    fit_name TEXT
);

CREATE TABLE color_variations (
    unique_color_id VARCHAR(100) PRIMARY KEY,
    unique_fit_id VARCHAR(100) REFERENCES fit_variations(unique_fit_id),
    main_product_id VARCHAR(100) REFERENCES main_products(main_product_id),
    color_product_id TEXT,
    color_name TEXT,
    color_image_url TEXT,
    color_url TEXT,
    style TEXT,
    shown TEXT
);

CREATE TABLE size_availability (
    unique_size_id VARCHAR(100) PRIMARY KEY,
    unique_color_id VARCHAR(100) REFERENCES color_variations(unique_color_id),
    unique_fit_id VARCHAR(100) REFERENCES fit_variations(unique_fit_id),
    color_product_id TEXT,
    main_product_id TEXT,
    color_name TEXT,
    fit_name TEXT,
    size TEXT,
    size_label TEXT,
    available BOOLEAN,
    price NUMERIC,
    original_price NUMERIC,
    discount_percent NUMERIC,
);

CREATE TABLE historical_changes (
    unique_size_id varchar(100) PRIMARY KEY,
    unique_color_id TEXT,
    color_product_id TEXT,
    size TEXT,
    size_label TEXT,
    timestamp TEXT,
    available BOOLEAN,
    price FLOAT,
    original_price FLOAT,
    discount_percent FLOAT,
    change_type TEXT,
);
