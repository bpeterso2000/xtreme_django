import django.http as http
import logging  # For logging errors
from fasttags.core import FT  # Import the FastTag class from FastTags
from fasttags.rendering import to_xml  # Import the rendering function
from fasttags.exceptions import CurativeError  # If available; otherwise, remove or handle generally

# Set up logging
logger = logging.getLogger(__name__)

def ft(view_func):
    """
    Django decorator to automatically render FastTag objects returned from a view.
    
    This decorator checks if the view's response is a FastTag object (or a list/dict containing them).
    If it is, it renders the FastTag(s) to HTML using FastTags' to_xml() function and returns an HttpResponse.
    Otherwise, it passes the response through unchanged.
    
    Enhanced with complete exception handling to catch and log errors, ensuring the application doesn't crash.
    
    Usage:
    @ft
    def my_view(request):
        return FT('div', "Hello from FastTags!")  # This will be rendered automatically
    
    Note: This is a basic implementation. Customize as needed for your project.
    """
    def wrapper(request, *args, **kwargs):
        try:
            # First, call the view function
            response = view_func(request, *args, **kwargs)
        except Exception as e:
            # Log the exception and return an error response
            logger.error(f"Exception in view function: {e}")
            return http.HttpResponse("An internal server error occurred. Please check the logs.", status=500)
        
        try:
            if isinstance(response, FT):
                # Render a single FastTag object
                try:
                    rendered_html = to_xml(response)
                    return http.HttpResponse(rendered_html)
                except CurativeError as e:  # Specific to FastTags if available
                    logger.error(f"CurativeError while rendering FastTag: {e}")
                    return http.HttpResponse("Error rendering FastTag: Invalid or unhealable content.", status=500)
                except Exception as e:  # General exceptions
                    logger.error(f"Error rendering FastTag: {e}")
                    return http.HttpResponse("An error occurred while rendering the FastTag.", status=500)
            
            elif isinstance(response, list):
                # Handle a list containing FastTag objects
                try:
                    rendered_items = []
                    for item in response:
                        if isinstance(item, FT):
                            rendered_items.append(to_xml(item))
                        else:
                            rendered_items.append(str(item))  # Or handle differently
                    rendered_html = ''.join(rendered_items)  # Concatenate
                    return http.HttpResponse(rendered_html)
                except CurativeError as e:
                    logger.error(f"CurativeError while processing list: {e}")
                    return http.HttpResponse("Error processing list: Invalid content encountered.", status=500)
                except Exception as e:
                    logger.error(f"Error processing list: {e}")
                    return http.HttpResponse("An error occurred while processing the list.", status=500)
            
            elif isinstance(response, dict):
                # Handle a dict containing FastTag objects (e.g., render values)
                try:
                    rendered_dict = {}
                    for key, value in response.items():
                        if isinstance(value, FT):
                            rendered_dict[key] = to_xml(value)
                        else:
                            rendered_dict[key] = str(value)  # Or handle differently
                    rendered_html = ''.join(str(rendered_dict.get(key)) for key in rendered_dict)  # Basic rendering
                    return http.HttpResponse(rendered_html)
                except CurativeError as e:
                    logger.error(f"CurativeError while processing dict: {e}")
                    return http.HttpResponse("Error processing dictionary: Invalid content encountered.", status=500)
                except Exception as e:
                    logger.error(f"Error processing dict: {e}")
                    return http.HttpResponse("An error occurred while processing the dictionary.", status=500)
            
            # If the response is not a FastTag, list, or dict, return it as-is
            return response
        
        except Exception as e:
            # Catch any unhandled exceptions in the outer try block
            logger.error(f"Unhandled exception in decorator: {e}")
            return http.HttpResponse("An internal server error occurred in the decorator.", status=500)
    
    return wrapper
