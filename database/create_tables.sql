-- Create FanWeights table if not exists
CREATE TABLE IF NOT EXISTS FanWeights (
    "Fan Model" TEXT NOT NULL,
    "Fan Size" TEXT NOT NULL,
    "Class" TEXT NOT NULL,
    "Arrangement" INTEGER NOT NULL,
    "Bare Fan Weight" INTEGER NOT NULL,
    "Unitary Base Frame" REAL,
    "Isolation Base Frame" REAL,
    "Split Casing" REAL,
    "Inlet Companion Flange" REAL,
    "Outlet Companion Flange" REAL,
    "Inlet Butterfly Damper" REAL,
    "No. of Isolators" REAL,
    "Shaft Diameter" REAL,
    PRIMARY KEY ("Fan Model", "Fan Size", "Class", "Arrangement")
);

-- Create AccessoryWeights table
CREATE TABLE IF NOT EXISTS AccessoryWeights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fan_model TEXT NOT NULL,
    fan_size TEXT NOT NULL,
    accessory TEXT NOT NULL,
    weight REAL NOT NULL,
    is_custom INTEGER DEFAULT 0,
    UNIQUE(fan_model, fan_size, accessory)
);

-- Create VendorWeightDetails table if not exists
CREATE TABLE IF NOT EXISTS VendorWeightDetails (
    "Vendor" TEXT NOT NULL,
    "WeightStart" INTEGER NOT NULL,
    "WeightEnd" INTEGER NOT NULL,
    "MSPrice" INTEGER NOT NULL,
    "SS304Price" INTEGER NOT NULL,
    PRIMARY KEY ("Vendor", "WeightStart", "WeightEnd")
);

-- Create BearingLookup table if not exists
CREATE TABLE IF NOT EXISTS BearingLookup (
    "Brand" TEXT NOT NULL,
    "Shaft Dia" INTEGER NOT NULL,
    "Description" TEXT,
    "Bearing" REAL,
    "Plummer block" REAL,
    "Sleeve" TEXT,
    "Total" REAL,
    PRIMARY KEY ("Brand", "Shaft Dia")
);

-- Create DrivePackLookup table if not exists
CREATE TABLE IF NOT EXISTS DrivePackLookup (
    "Motor kW" REAL NOT NULL,
    "Drive Pack" INTEGER NOT NULL,
    "Weight" REAL,
    PRIMARY KEY ("Motor kW")
);

-- Create EnquiryFans table if not exists
CREATE TABLE IF NOT EXISTS EnquiryFans (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "enquiry_number" TEXT NOT NULL,
    "customer_name" TEXT NOT NULL,
    "fan_number" INTEGER NOT NULL,
    "specifications" TEXT NOT NULL,
    "accessories" TEXT,
    "vendor" TEXT,
    "material" TEXT,
    "vibration_isolators" TEXT,
    "optional_items" TEXT,
    "motor_brand" TEXT,
    "motor_kw" TEXT,
    "motor_pole" TEXT,
    "motor_efficiency" TEXT,
    "bearing_brand" TEXT,
    "bearing_kw" TEXT,
    "bearing_pole" TEXT,
    "bearing_efficiency" TEXT,
    "fabrication_margin" REAL,
    "bought_out_margin" REAL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MotorPrices table if not exists
CREATE TABLE IF NOT EXISTS MotorPrices (
    "Brand" TEXT NOT NULL,
    "Motor kW" TEXT NOT NULL,
    "Pole" TEXT NOT NULL,
    "Efficiency" TEXT NOT NULL,
    "Price" REAL NOT NULL,
    PRIMARY KEY ("Brand", "Motor kW", "Pole", "Efficiency")
);

-- Insert sample motor prices
INSERT OR IGNORE INTO MotorPrices ("Brand", "Motor kW", "Pole", "Efficiency", "Price") VALUES
    ('ABB', '0.75', '4', 'IE2', 8500),
    ('ABB', '1.1', '4', 'IE2', 10500),
    ('ABB', '1.5', '4', 'IE2', 12500),
    ('ABB', '2.2', '4', 'IE2', 15500),
    ('ABB', '3.7', '4', 'IE2', 22000),
    ('ABB', '5.5', '4', 'IE2', 28000),
    ('ABB', '7.5', '4', 'IE2', 35000),
    ('ABB', '11', '4', 'IE2', 45000),
    ('ABB', '15', '4', 'IE2', 58000),
    ('ABB', '18.5', '4', 'IE2', 68000),
    ('ABB', '22', '4', 'IE2', 78000),
    ('ABB', '30', '4', 'IE2', 95000),
    ('ABB', '37', '4', 'IE2', 115000),
    ('ABB', '45', '4', 'IE2', 135000),
    ('ABB', '55', '4', 'IE2', 165000),
    ('ABB', '75', '4', 'IE2', 210000),
    ('ABB', '90', '4', 'IE2', 245000),
    ('ABB', '110', '4', 'IE2', 285000),
    ('ABB', '132', '4', 'IE2', 335000),
    ('ABB', '160', '4', 'IE2', 395000),
    ('ABB', '200', '4', 'IE2', 475000),
    ('ABB', '250', '4', 'IE2', 575000),
    ('ABB', '315', '4', 'IE2', 695000),
    ('ABB', '355', '4', 'IE2', 785000),
    ('ABB', '400', '4', 'IE2', 885000),
    ('Siemens', '0.75', '4', 'IE2', 8000),
    ('Siemens', '1.1', '4', 'IE2', 10000),
    ('Siemens', '1.5', '4', 'IE2', 12000),
    ('Siemens', '2.2', '4', 'IE2', 15000),
    ('Siemens', '3.7', '4', 'IE2', 21000),
    ('Siemens', '5.5', '4', 'IE2', 27000),
    ('Siemens', '7.5', '4', 'IE2', 34000),
    ('Siemens', '11', '4', 'IE2', 44000),
    ('Siemens', '15', '4', 'IE2', 57000),
    ('Siemens', '18.5', '4', 'IE2', 67000),
    ('Siemens', '22', '4', 'IE2', 77000),
    ('Siemens', '30', '4', 'IE2', 94000),
    ('Siemens', '37', '4', 'IE2', 114000),
    ('Siemens', '45', '4', 'IE2', 134000),
    ('Siemens', '55', '4', 'IE2', 164000),
    ('Siemens', '75', '4', 'IE2', 209000),
    ('Siemens', '90', '4', 'IE2', 244000),
    ('Siemens', '110', '4', 'IE2', 284000),
    ('Siemens', '132', '4', 'IE2', 334000),
    ('Siemens', '160', '4', 'IE2', 394000),
    ('Siemens', '200', '4', 'IE2', 474000),
    ('Siemens', '250', '4', 'IE2', 574000),
    ('Siemens', '315', '4', 'IE2', 694000),
    ('Siemens', '355', '4', 'IE2', 784000),
    ('Siemens', '400', '4', 'IE2', 884000),
    ('Crompton', '0.75', '4', 'IE2', 7500),
    ('Crompton', '1.1', '4', 'IE2', 9500),
    ('Crompton', '1.5', '4', 'IE2', 11500),
    ('Crompton', '2.2', '4', 'IE2', 14500),
    ('Crompton', '3.7', '4', 'IE2', 20000),
    ('Crompton', '5.5', '4', 'IE2', 26000),
    ('Crompton', '7.5', '4', 'IE2', 33000),
    ('Crompton', '11', '4', 'IE2', 43000),
    ('Crompton', '15', '4', 'IE2', 56000),
    ('Crompton', '18.5', '4', 'IE2', 66000),
    ('Crompton', '22', '4', 'IE2', 76000),
    ('Crompton', '30', '4', 'IE2', 93000),
    ('Crompton', '37', '4', 'IE2', 113000),
    ('Crompton', '45', '4', 'IE2', 133000),
    ('Crompton', '55', '4', 'IE2', 163000),
    ('Crompton', '75', '4', 'IE2', 208000),
    ('Crompton', '90', '4', 'IE2', 243000),
    ('Crompton', '110', '4', 'IE2', 283000),
    ('Crompton', '132', '4', 'IE2', 333000),
    ('Crompton', '160', '4', 'IE2', 393000),
    ('Crompton', '200', '4', 'IE2', 473000),
    ('Crompton', '250', '4', 'IE2', 573000),
    ('Crompton', '315', '4', 'IE2', 693000),
    ('Crompton', '355', '4', 'IE2', 783000),
    ('Crompton', '400', '4', 'IE2', 883000);

-- Add IE3 prices (20% higher than IE2)
INSERT OR IGNORE INTO MotorPrices ("Brand", "Motor kW", "Pole", "Efficiency", "Price")
SELECT 
    "Brand",
    "Motor kW",
    "Pole",
    'IE3',
    ROUND("Price" * 1.2, 0)
FROM MotorPrices
WHERE "Efficiency" = 'IE2';

-- Add 2-pole prices (10% higher than 4-pole)
INSERT OR IGNORE INTO MotorPrices ("Brand", "Motor kW", "Pole", "Efficiency", "Price")
SELECT 
    "Brand",
    "Motor kW",
    '2',
    "Efficiency",
    ROUND("Price" * 1.1, 0)
FROM MotorPrices
WHERE "Pole" = '4';

-- Add 6-pole prices (15% higher than 4-pole)
INSERT OR IGNORE INTO MotorPrices ("Brand", "Motor kW", "Pole", "Efficiency", "Price")
SELECT 
    "Brand",
    "Motor kW",
    '6',
    "Efficiency",
    ROUND("Price" * 1.15, 0)
FROM MotorPrices
WHERE "Pole" = '4';

-- Add 8-pole prices (25% higher than 4-pole)
INSERT OR IGNORE INTO MotorPrices ("Brand", "Motor kW", "Pole", "Efficiency", "Price")
SELECT 
    "Brand",
    "Motor kW",
    '8',
    "Efficiency",
    ROUND("Price" * 1.25, 0)
FROM MotorPrices
WHERE "Pole" = '4'; 