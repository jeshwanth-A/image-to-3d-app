"""
Utility script to check if blueprints are properly defined and registered.
Run this file directly to diagnose blueprint issues.
"""
import os
import sys
import importlib
import inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_blueprint(module_name):
    """Check if a module contains a Flask blueprint."""
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        logger.info(f"✓ Successfully imported {module_name}")
        
        # Find blueprints in the module
        blueprints = []
        for name, obj in inspect.getmembers(module):
            if name.endswith('_bp') or name.endswith('_blueprint'):
                blueprints.append((name, obj))
        
        if blueprints:
            logger.info(f"✓ Found {len(blueprints)} blueprints in {module_name}:")
            for name, bp in blueprints:
                logger.info(f"  - {name} (url_prefix: {bp.url_prefix})")
                
                # Check for routes
                routes = []
                for rule in bp.deferred_functions:
                    if hasattr(rule, '__name__') and rule.__name__ == 'deferred':
                        routes.append(rule)
                
                logger.info(f"    Has {len(routes)} routes defined")
            
            return True
        else:
            logger.warning(f"✗ No blueprints found in {module_name}")
            return False
    
    except ImportError as e:
        logger.error(f"✗ Could not import {module_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error checking {module_name}: {e}")
        return False

if __name__ == "__main__":
    # Check common blueprint modules
    modules_to_check = ['auth', 'upload', 'routes']
    
    logger.info("Checking Flask blueprints...")
    
    results = {}
    for module in modules_to_check:
        success = check_blueprint(module)
        results[module] = success
    
    # Summary
    logger.info("\nBLUEPRINT CHECK SUMMARY:")
    for module, success in results.items():
        status = "✓ OK" if success else "✗ Not found/Error"
        logger.info(f"{module}: {status}")
