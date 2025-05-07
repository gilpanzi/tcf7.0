import sqlite3

def check_fan_models():
    conn = sqlite3.connect('fan_weights.db')
    cursor = conn.cursor()
    
    # Get all unique fan models
    cursor.execute('SELECT DISTINCT "Fan Model" FROM FanWeights ORDER BY "Fan Model"')
    fan_models = cursor.fetchall()
    
    print("\nFan Models and their available sizes:")
    for model in fan_models:
        model_name = model[0]
        print(f"\nFan Model: {model_name}")
        
        # Get available sizes for this model
        cursor.execute('SELECT DISTINCT "Fan Size" FROM FanWeights WHERE "Fan Model" = ? ORDER BY "Fan Size"', (model_name,))
        sizes = cursor.fetchall()
        print("Available sizes:")
        for size in sizes:
            print(f"  - {size[0]}")
            
            # Get available classes for this model and size
            cursor.execute('SELECT DISTINCT "Class" FROM FanWeights WHERE "Fan Model" = ? AND "Fan Size" = ?', (model_name, size[0]))
            classes = cursor.fetchall()
            print("    Classes:")
            for class_ in classes:
                print(f"      * {class_[0]}")
                
                # Get available arrangements for this combination
                cursor.execute('''
                    SELECT DISTINCT "Arrangement" 
                    FROM FanWeights 
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ?
                ''', (model_name, size[0], class_[0]))
                arrangements = cursor.fetchall()
                print("        Arrangements:", [arr[0] for arr in arrangements])
    
    conn.close()

if __name__ == "__main__":
    check_fan_models() 