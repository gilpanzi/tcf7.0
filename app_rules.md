# TCF Pricing Tool Application Rules

## Restricted Changes
1. Bought Out Calculations:
   - No changes allowed to existing calculation logic
   - Maintain current formulas and methods
   - Preserve all existing validation rules

2. Motor and Isolators Section:
   - No modifications to existing functionality
   - Keep current calculation methods
   - Maintain existing validation rules

3. Bearings and Drive Pack Section:
   - No changes to current implementation
   - Preserve existing calculation logic
   - Maintain current validation rules

4. Optional Items:
   - No modifications to custom optional items
   - No changes to standard optional items
   - Preserve existing calculation and validation logic

## Database Rules
1. Always check the database schema in `database/create_tables.sql` before making any database-related changes
2. Ensure all new tables have proper primary keys and foreign key constraints
3. Maintain data integrity by using appropriate data types and constraints
4. Document any schema changes in the migration system

## Frontend Rules
1. Always check `static/js/main.js` for existing functionality before adding new features
2. Follow the established pattern for:
   - Form validation
   - Error handling
   - Modal management
   - Event handling
3. Maintain consistent UI/UX patterns:
   - Use the same modal structure
   - Follow the same error message format
   - Use consistent button styles and placements
4. Ensure all user inputs are properly validated
5. Maintain proper state management between pages

## Backend Rules
1. Always check `routes.py` for existing routes and functionality
2. Follow the established pattern for:
   - Route handlers
   - Error responses
   - Session management
   - Database operations
3. Ensure proper error handling and logging
4. Maintain consistent response formats
5. Validate all inputs before processing

## Calculation Rules
1. Always verify calculation formulas against the business requirements
2. Maintain proper precision for financial calculations
3. Document any changes to calculation logic
4. Ensure all calculations are properly validated
5. Maintain consistency in rounding and decimal places

## Testing Rules
1. Verify changes work in all scenarios:
   - New fan entry
   - Edit existing fan
   - Project management
   - Accessory handling
2. Test edge cases and error conditions
3. Ensure backward compatibility
4. Verify data persistence

## Security Rules
1. Always validate user inputs
2. Maintain proper session management
3. Ensure proper access control
4. Protect sensitive data
5. Follow secure coding practices

## Documentation Rules
1. Document all new features
2. Update existing documentation when making changes
3. Maintain clear code comments
4. Document any assumptions or limitations

## Code Review Checklist
Before making any changes, verify:
1. The change aligns with existing patterns
2. All dependencies are properly handled
3. Error cases are covered
4. Performance impact is considered
5. Security implications are addressed
6. Documentation is updated
7. Testing is possible
8. Backward compatibility is maintained
9. Changes do not affect restricted sections:
    - Bought out calculations
    - Motor and Isolators section
    - Bearings and Drive pack section
    - Custom and standard optional items

## Change Process
1. Review existing code and patterns
2. Plan the change
3. Make the change
4. Test thoroughly
5. Document the change
6. Verify backward compatibility
7. Check for any unintended side effects 
8. Always check front end and back end items are matching. 