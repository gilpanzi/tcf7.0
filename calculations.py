import logging

logger = logging.getLogger(__name__)

ACCESSORY_NAME_MAP = {
    'unitary_base_frame': 'Unitary Base Frame',
    'isolation_base_frame': 'Isolation Base Frame',
    'split_casing': 'Split Casing',
    'inlet_companion_flange': 'Inlet Companion Flange',
    'outlet_companion_flange': 'Outlet Companion Flange',
    'inlet_butterfly_damper': 'Inlet Butterfly Damper'
}

def calculate_fan_weight(cursor, fan_data, selected_accessories):
    """Calculate fan weight and related data."""
    try:
        # Skip DB lookup for custom materials
        if fan_data.get('material') == 'others':
            logger.info("Skipping DB fan weights for custom material entry")
            return 0, 0, 0, 0, None, {}
            
        cursor.execute('''
            SELECT * FROM FanWeights 
            WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
        ''', (fan_data['Fan Model'], fan_data['Fan Size'], fan_data['Class'], fan_data['Arrangement']))
        
        fan_weight_row = cursor.fetchone()
        if not fan_weight_row:
            return None, None, None, None, "Fan weight data not found", {}
        
        fan_weight_dict = dict(zip([column[0] for column in cursor.description], fan_weight_row))
        
        # Bare fan weight
        bare_fan_weight = float(fan_weight_dict['Bare Fan Weight']) if fan_weight_dict['Bare Fan Weight'] is not None else None
        if bare_fan_weight is None:
            return None, None, None, None, "Invalid or missing bare fan weight", {}

        total_weight = bare_fan_weight

        # No. of isolators
        no_of_isolators = int(fan_weight_dict['No. of Isolators']) if fan_weight_dict['No. of Isolators'] is not None else None

        # Shaft diameter
        shaft_diameter = float(fan_weight_dict['Shaft Diameter']) if fan_weight_dict['Shaft Diameter'] is not None else None

        # Accessory weights (standard)
        accessory_details = {}
        for raw_accessory in selected_accessories:
            accessory = ACCESSORY_NAME_MAP.get(raw_accessory, raw_accessory)
            if accessory in fan_weight_dict and fan_weight_dict[accessory] is not None:
                try:
                    accessory_weight = float(fan_weight_dict[accessory])
                    total_weight += accessory_weight
                    accessory_details[accessory] = accessory_weight
                    logger.info(f"Found weight for {accessory}: {accessory_weight} kg")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid weight value for {accessory}")
                    accessory_details[accessory] = None
            else:
                logger.warning(f"Weight not found for {accessory} in FanWeights table")
                accessory_details[accessory] = None

        # Custom accessories
        if 'customAccessories' in fan_data and isinstance(fan_data['customAccessories'], dict):
            for name, weight in fan_data['customAccessories'].items():
                try:
                    custom_weight = float(weight)
                    total_weight += custom_weight
                    accessory_details[name] = custom_weight
                    logger.info(f"Added custom accessory: {name} = {custom_weight} kg")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid custom accessory weight for {name}")
                    accessory_details[name] = None

        return bare_fan_weight, no_of_isolators, shaft_diameter, total_weight, None, accessory_details

    except Exception as e:
        logger.error(f"Error in calculate_fan_weight: {str(e)}", exc_info=True)
        return None, None, None, None, f"Error calculating fan weight: {str(e)}", {}

def calculate_fabrication_cost(cursor, fan_data, total_weight):
    """Calculate fabrication cost based on vendor and material."""
    try:
        vendor = fan_data.get('vendor', 'TCF Factory')
        material = fan_data.get('material', 'ms')
        logger.info(f"Calculating fabrication cost for vendor: {vendor}, material: {material}")
        
        # Handle custom materials ('others' type)
        if material == 'others':
            logger.info("Processing custom materials calculation")
            
            # Debug logging for custom material values
            for i in range(5):
                logger.info(f"Material {i} from frontend: name={fan_data.get(f'material_name_{i}')}, weight={fan_data.get(f'material_weight_{i}')}, rate={fan_data.get(f'material_rate_{i}')}")
            
            fabrication_cost = 0
            total_weight = 0
            custom_weights = {}
            
            # Process up to 5 custom materials
            for i in range(5):
                weight_key = f'material_weight_{i}'
                rate_key = f'material_rate_{i}'
                name_key = f'material_name_{i}'
                
                # Check if both weight and rate are present
                if weight_key in fan_data and rate_key in fan_data:
                    try:
                        material_weight = float(fan_data[weight_key])
                        material_rate = float(fan_data[rate_key])
                        material_name = fan_data.get(name_key, f'Material {i+1}')
                        
                        if material_weight > 0 and material_rate > 0:
                            component_cost = material_weight * material_rate
                            fabrication_cost += component_cost
                            total_weight += material_weight
                            custom_weights[material_name] = {
                                'weight': material_weight,
                                'rate': material_rate,
                                'cost': component_cost
                            }
                            logger.info(f"Added {material_name}: weight={material_weight}, rate={material_rate}, cost={component_cost}")
                        else:
                            logger.warning(f"Invalid weight or rate for custom material {i}: weight={material_weight}, rate={material_rate}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error processing custom material {i}: {str(e)}")
                else:
                    logger.warning(f"Missing weight or rate for custom material {i}")
            
            logger.info(f"Total fabrication cost for custom materials: {fabrication_cost}")
            return fabrication_cost, total_weight, custom_weights, None
        
        # For standard materials (MS, SS304, mixed)
        logger.info(f"Looking up rate for vendor: {vendor}, weight: {total_weight}")
        cursor.execute('''
            SELECT MSPrice, SS304Price FROM VendorWeightDetails
            WHERE Vendor = ? AND WeightStart <= ? AND WeightEnd > ?
        ''', (vendor, total_weight, total_weight))
        
        vendor_row = cursor.fetchone()
        if not vendor_row:
            logger.error(f"No matching vendor price found for vendor: {vendor}, weight: {total_weight}")
            return None, None, None, {
                'error': 'No matching vendor price found',
                'details': {
                    'vendor': vendor,
                    'weight': total_weight
                }
            }
        
        ms_price = vendor_row['MSPrice']
        ss304_price = vendor_row['SS304Price']
        logger.debug(f"Vendor prices - MS: {ms_price}, SS304: {ss304_price}")
        
        # Calculate fabrication cost based on material
        if material == 'ms':
            fabrication_cost = total_weight * ms_price
        elif material == 'ss304':
            fabrication_cost = total_weight * ss304_price
        elif material == 'mixed':
            ms_percentage = float(fan_data.get('ms_percentage', 0))
            if ms_percentage <= 0 or ms_percentage > 100:
                logger.error(f"Invalid MS percentage for mixed construction: {ms_percentage}")
                return None, None, None, {
                    'error': 'Invalid MS percentage for mixed construction',
                    'details': {
                        'ms_percentage': ms_percentage
                    }
                }
            
            # Calculate weights based on percentages
            ms_weight = total_weight * (ms_percentage / 100)
            ss_weight = total_weight * ((100 - ms_percentage) / 100)
            
            fabrication_cost = (ms_weight * ms_price) + (ss_weight * ss304_price)
        else:
            fabrication_cost = total_weight * ms_price
        
        logger.info(f"Fabrication cost calculated: {fabrication_cost}")
        return fabrication_cost, total_weight, {}, None
        
    except Exception as e:
        logger.error(f"Error calculating fabrication cost: {str(e)}", exc_info=True)
        return None, None, None, {
            'error': 'Error calculating fabrication cost',
            'details': str(e)
        }

def calculate_bought_out_components(cursor, fan_data, no_of_isolators, shaft_diameter):
    """Calculate costs for bought out components."""
    logger.info(f"Calculating bought out components with data: {fan_data}")
    
    try:
        # Initialize values
        vibration_isolators_price = 0
        bearing_price = 0
        drive_pack_price = 0
        motor_list_price = 0
        
        # Get bearing brand from fan_data
        bearing_brand = fan_data.get('bearing_brand', 'SKF')  # Default to SKF if not specified
        
        # Calculate vibration isolators price if needed
        if 'vibration_isolators' in fan_data:
            if fan_data['vibration_isolators'] == 'polybond':
                vibration_isolators_price = no_of_isolators * 1000 if no_of_isolators else 0
            elif fan_data['vibration_isolators'] == 'dunlop':
                vibration_isolators_price = no_of_isolators * 2000 if no_of_isolators else 0
        
        # Get bearing price from frontend data if available
        if 'bearing_price' in fan_data and fan_data['bearing_price']:
            bearing_price = float(fan_data['bearing_price'])
            if fan_data['Arrangement'] != 4:
                bearing_price = bearing_price * 2
        elif fan_data['Arrangement'] != 4 and shaft_diameter:
            cursor.execute('''
                SELECT * FROM BearingLookup
                WHERE Brand = ? AND ShaftDiameter = ?
            ''', (bearing_brand, shaft_diameter))
            bearing_row = cursor.fetchone()
            
            if not bearing_row:
                cursor.execute('''
                    SELECT * FROM BearingLookup
                    WHERE Brand = ? AND ShaftDiameter > ?
                    ORDER BY ShaftDiameter ASC
                    LIMIT 1
                ''', (bearing_brand, shaft_diameter))
                bearing_row = cursor.fetchone()
            
            if bearing_row:
                columns = [description[0] for description in cursor.description]
                bearing_dict = dict(zip(columns, bearing_row))
                bearing_price = bearing_dict.get('Total', 0)
                if fan_data['Arrangement'] != 4:
                    bearing_price = bearing_price * 2
        
        # Calculate Drive Pack cost
        drive_pack_kw = fan_data.get('drive_pack') or fan_data.get('drive_pack_kw')
        if drive_pack_kw and fan_data['Arrangement'] != '4':  # Only calculate if not arrangement 4
            try:
                # Convert to float and ensure proper format
                drive_pack_kw = float(drive_pack_kw)
                logger.info(f"Looking up drive pack cost for {drive_pack_kw} kW")
                
                # Query the DrivePackLookup table
                cursor.execute('SELECT "Drive Pack" FROM DrivePackLookup WHERE "Motor kW" = ?', (drive_pack_kw,))
                result = cursor.fetchone()
                
                if result:
                    drive_pack_price = float(result[0])
                    logger.info(f"Found drive pack price: ₹{drive_pack_price} for {drive_pack_kw} kW")
                else:
                    logger.warning(f"No drive pack cost found for kW: {drive_pack_kw}")
                    # Log available options for debugging
                    cursor.execute('SELECT "Motor kW" FROM DrivePackLookup ORDER BY "Motor kW"')
                    available_kw = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Available kW options: {available_kw}")
            except Exception as e:
                logger.error(f"Error looking up drive pack cost: {e}")
                drive_pack_price = 0
        
        # Get motor list price
        motor_brand = fan_data.get('Motor Brand', fan_data.get('motor_brand', ''))
        motor_kw = None
        if 'Motor kW' in fan_data and fan_data['Motor kW'] is not None:
            try:
                motor_kw = float(fan_data['Motor kW'])
            except (ValueError, TypeError):
                pass
        elif 'motor_kw' in fan_data and fan_data['motor_kw'] is not None:
            try:
                motor_kw = float(fan_data['motor_kw'])
            except (ValueError, TypeError):
                pass
        
        pole = fan_data.get('Pole', fan_data.get('pole', ''))
        efficiency = fan_data.get('Efficiency', fan_data.get('efficiency', ''))
        motor_discount = float(fan_data.get('motor_discount', 0))
        
        # Initialize discounted price same as list price initially
        discounted_motor_price = 0 

        if motor_kw and motor_kw > 0 and motor_brand and pole and efficiency:
            cursor.execute('''
                SELECT "Price" FROM MotorPrices
                WHERE "Motor kW" = ? AND "Pole" = ? AND "Brand" = ? AND "Efficiency" = ?
            ''', (motor_kw, pole, motor_brand, efficiency))
            
            motor_price_row = cursor.fetchone()
            if motor_price_row:
                motor_list_price = motor_price_row[0]
                # Apply discount if any
                discounted_motor_price = motor_list_price  # Start with list price
                if motor_discount > 0:
                    # Calculate the discounted price
                    discounted_motor_price = motor_list_price * (1 - motor_discount / 100)
        
        # Calculate total bought out cost using the discounted motor price
        total_cost = vibration_isolators_price + bearing_price + drive_pack_price + discounted_motor_price
        logger.info(f"Total bought out cost calculated: {total_cost}")
        logger.info(f"Individual component prices: VI={vibration_isolators_price}, B={bearing_price}, DP={drive_pack_price}, M_List={motor_list_price}, M_Discounted={discounted_motor_price}")
        
        return {
            'total_cost': total_cost,
            'vibration_isolators_price': vibration_isolators_price,
            'bearing_price': bearing_price,
            'drive_pack_price': drive_pack_price,
            'motor_list_price': motor_list_price,          # Original list price
            'discounted_motor_price': discounted_motor_price, # Price after discount
            'motor_discount': motor_discount
        }, None
        
    except Exception as e:
        logger.error(f"Error calculating bought out components: {str(e)}", exc_info=True)
        return None, {
            'error': 'Error calculating bought out components',
            'details': str(e)
        }

def calculate_fan_price(data, db_connection):
    """Calculate the total fan price based on input data."""
    cursor = db_connection.cursor()
    total_price = 0
    
    # Get motor price
    cursor.execute('''
        SELECT "Price"
        FROM MotorPrices
        WHERE "Motor kW" = ? AND "Pole" = ? AND "Efficiency" = ?
    ''', (data['Motor kW'], data['Pole'], data['Efficiency']))
    motor_result = cursor.fetchone()
    if not motor_result:
        raise ValueError("Motor specifications not found in database")
    motor_price = float(motor_result[0])
    total_price += motor_price

    # Get bearing price
    cursor.execute('''
        SELECT "Price"
        FROM BearingLookup
        WHERE "Shaft Dia" = ?
    ''', (data['Shaft Dia'],))
    bearing_result = cursor.fetchone()
    if not bearing_result:
        raise ValueError("Bearing specifications not found in database")
    bearing_price = float(bearing_result[0])
    total_price += bearing_price

    # Calculate accessory weights and prices
    accessory_weight = 0
    for accessory in data.get('accessories', []):
        cursor.execute(f'''
            SELECT "{accessory}"
            FROM FanWeights
            WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
        ''', (
            data['Fan Model'],
            data['Fan Size'],
            data['Class'],
            data['Arrangement']
        ))
        weight_result = cursor.fetchone()
        if not weight_result or weight_result[0] is None:
            raise ValueError(f"Weight not found for accessory: {accessory}")
        accessory_weight += float(weight_result[0])

    # Get vendor weight details
    cursor.execute('''
        SELECT "Price Per KG"
        FROM VendorWeightDetails
        WHERE "Material Type" = ?
    ''', (data['Material Type'],))
    vendor_result = cursor.fetchone()
    if not vendor_result:
        raise ValueError("Material type not found in database")
    price_per_kg = float(vendor_result[0])

    # Calculate material cost based on total weight
    total_weight = accessory_weight  # Add base weight if needed
    material_cost = total_weight * price_per_kg
    total_price += material_cost

    return {
        'total_price': round(total_price, 2),
        'motor_price': round(motor_price, 2),
        'bearing_price': round(bearing_price, 2),
        'material_cost': round(material_cost, 2),
        'total_weight': round(total_weight, 2)
    } 