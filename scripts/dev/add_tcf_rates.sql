-- Add TCF Factory rates for different weight ranges
INSERT INTO VendorWeightDetails (Vendor, WeightStart, WeightEnd, MSPrice, SS304Price)
VALUES 
    ('TCF Factory', 0, 75, 200, 500),
    ('TCF Factory', 75, 150, 190, 500),
    ('TCF Factory', 150, 750, 180, 500),
    ('TCF Factory', 750, 1500, 170, 500),
    ('TCF Factory', 1500, 10000, 160, 500); 