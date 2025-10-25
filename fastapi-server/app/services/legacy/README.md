# Legacy Services

These services are from the previous version of the application (homeless assistance system) and are kept here for reference only.

## Archived Services

- **claude.py** - Original Claude AI integration for workflow routing
- **medical.py** - Medical facility locator
- **pharmacy.py** - Pharmacy finder with appointment availability
- **shelter.py** - Homeless shelter locator
- **restroom.py** - Public restroom finder

## Status

These services are **deprecated** and not used in the current auto-reorder system. They are kept for backward compatibility or historical reference.

If you need to restore any functionality from these services, you can reference the code here, but they are not actively maintained.

## Migration Notes

The current system uses:
- `vision_ai.py` instead of `claude.py` for AI/ML tasks
- `product_service.py` for product management
- `order_service.py` for commerce integration
- `user_service.py` for user management

Location-based services have been removed in favor of the product-centric auto-reorder system.

