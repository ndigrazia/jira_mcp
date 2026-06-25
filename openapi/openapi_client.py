import os
import json
import base64
import re
import logging
import inspect
from typing import Any, Dict, List, Optional, Tuple
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("openapi-client")

class OpenAPIClient:
    """A generic client to parse OpenAPI/Swagger specs and perform HTTP requests."""
    
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.swagger_data = self._load_swagger()
        self.client_holder: Dict[str, Optional[httpx.AsyncClient]] = {"client": None}

    def _load_swagger(self) -> Dict[str, Any]:
        """Load the Swagger/OpenAPI JSON specification."""
        try:
            with open(self.swagger_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load swagger.json: {e}")
            return {}

    def resolve_ref(self, ref_str: str) -> Dict[str, Any]:
        """Resolve a $ref pointer in the Swagger document."""
        if not ref_str or not ref_str.startswith("#/"):
            return {}
        parts = ref_str.split("/")[1:]
        current = self.swagger_data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return {}
        return current

    def get_python_type(self, schema: Dict[str, Any]) -> Any:
        """Map OpenAPI/Swagger schema types to Python types."""
        if "$ref" in schema:
            resolved = self.resolve_ref(schema["$ref"])
            return self.get_python_type(resolved)
        
        t = schema.get("type", "string")
        if t == "string":
            return str
        elif t == "integer":
            return int
        elif t == "number":
            return float
        elif t == "boolean":
            return bool
        elif t == "array":
            return list
        elif t == "object":
            return dict
        return Any

    def sanitize_name(self, name: str) -> str:
        """Sanitize operation names to be valid python/tool names."""
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != "_":
            sanitized = "_" + sanitized
        return sanitized

    def get_client(self) -> httpx.AsyncClient:
        """Get or create the global httpx.AsyncClient."""
        if self.client_holder["client"] is None or self.client_holder["client"].is_closed:
            base_url = os.environ.get("JIRA_BASE_URL", "https://your-domain.atlassian.net").rstrip("/")
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Configure Basic Authentication
            username = os.environ.get("JIRA_USERNAME")
            api_token = os.environ.get("JIRA_API_TOKEN")
            if username and api_token:
                auth_str = f"{username}:{api_token}"
                auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
                headers["Authorization"] = f"Basic {auth_b64}"
                logger.info("OpenAPI client authentication configured.")
            else:
                logger.warning("Jira credentials not set. OpenAPI requests will be unauthenticated.")
                
            self.client_holder["client"] = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0)
        return self.client_holder["client"]

    def extract_operation_metadata(self, method: str, path_template: str, op_data: Dict[str, Any]) -> Tuple[str, str, str, Dict[str, Any], Dict[str, Any], Dict[str, Any], List[Tuple[str, Any, Any]]]:
        """Extract metadata for registering an OpenAPI operation as an MCP tool."""
        operation_id = op_data.get("operationId")
        if not operation_id:
            # Generate a name from method and path
            clean_path = path_template.replace("/rest/agile/1.0/", "").replace("/rest/devinfo/0.10/", "").replace("/rest/featureflags/0.1/", "")
            clean_path = re.sub(r"\{[^}]+\}", "", clean_path)
            parts = [method.lower()] + [p for p in clean_path.split("/") if p]
            operation_id = "_".join(parts)
            
        tool_name = self.sanitize_name(operation_id)
        summary = op_data.get("summary", "")
        description = op_data.get("description", "")
        
        path_params_info = {}
        query_params_info = {}
        body_params_info = {}
        
        raw_params = []
        seen_param_names = set()
        
        # 1. Parse parameters (path & query)
        parameters = op_data.get("parameters", [])
        for param in parameters:
            if "$ref" in param:
                param = self.resolve_ref(param["$ref"])
                
            p_name = param.get("name")
            p_in = param.get("in")
            p_schema = param.get("schema", {})
            
            p_type = self.get_python_type(p_schema)
            p_default = p_schema.get("default", None)
            
            if p_name in seen_param_names:
                continue
            seen_param_names.add(p_name)
            
            if p_in == "path":
                path_params_info[p_name] = p_type
                raw_params.append((p_name, p_type, inspect.Parameter.empty, f"(path) {param.get('description', '')}"))
            elif p_in == "query":
                query_params_info[p_name] = (p_type, p_default)
                default_val = p_default if p_default is not None else None
                raw_params.append((p_name, Optional[p_type], default_val, f"(query) {param.get('description', '')}"))

        # 2. Parse request body
        req_body = op_data.get("requestBody", {})
        if "$ref" in req_body:
            req_body = self.resolve_ref(req_body["$ref"])
            
        if req_body:
            content = req_body.get("content", {})
            json_content = content.get("application/json", {})
            body_schema = json_content.get("schema", {})
            if "$ref" in body_schema:
                body_schema = self.resolve_ref(body_schema["$ref"])
                
            # If the body is an object with defined properties, map top-level fields
            if body_schema.get("type") == "object" and "properties" in body_schema:
                properties = body_schema.get("properties", {})
                required_body_fields = body_schema.get("required", [])
                for prop_name, prop_schema in properties.items():
                    if "$ref" in prop_schema:
                        prop_schema = self.resolve_ref(prop_schema["$ref"])
                    prop_type = self.get_python_type(prop_schema)
                    prop_desc = prop_schema.get("description", "")
                    prop_required = prop_name in required_body_fields
                    
                    body_params_info[prop_name] = prop_type
                    
                    if prop_name in seen_param_names:
                        continue
                    seen_param_names.add(prop_name)
                    
                    default_val = inspect.Parameter.empty if prop_required else None
                    raw_params.append((prop_name, prop_type if prop_required else Optional[prop_type], default_val, f"(body) {prop_desc}"))
            else:
                if "body" not in seen_param_names:
                    seen_param_names.add("body")
                    body_params_info["body"] = dict
                    raw_params.append(("body", Optional[dict], None, "(body) JSON body matching schema."))

        # Sort raw_params: required parameters first (default is inspect.Parameter.empty), then optional
        params_list = []
        # Add required params
        for item in raw_params:
            if item[2] is inspect.Parameter.empty:
                params_list.append(item)
        # Add optional params
        for item in raw_params:
            if item[2] is not inspect.Parameter.empty:
                params_list.append(item)

        return tool_name, summary, description, path_params_info, query_params_info, body_params_info, params_list

    async def execute_request(self, method: str, path_template: str, path_params_info: Dict[str, Any], query_params_info: Dict[str, Any], body_params_info: Dict[str, Any], kwargs: Dict[str, Any]) -> Any:
        """Build the HTTP request and perform it asynchronously."""
        client = self.get_client()
        
        # Build URL from template
        url_path = path_template
        for p_name in path_params_info:
            if p_name in kwargs:
                url_path = url_path.replace(f"{{{p_name}}}", str(kwargs[p_name]))
                
        # Build Query Params
        query_args = {}
        for q_name, (q_type, q_default) in query_params_info.items():
            if q_name in kwargs and kwargs[q_name] is not None:
                query_args[q_name] = kwargs[q_name]
                
        # Build Request Body
        body_data = {}
        if "body" in body_params_info and "body" in kwargs and kwargs["body"] is not None:
            body_data = kwargs["body"]
        else:
            for b_name in body_params_info:
                if b_name in kwargs and kwargs[b_name] is not None:
                    body_data[b_name] = kwargs[b_name]
                    
        # Perform HTTP Request
        try:
            logger.info(f"OpenAPI Request: {method.upper()} {url_path} | Query: {query_args} | Body Keys: {list(body_data.keys())}")
            if method.lower() == "get":
                res = await client.get(url_path, params=query_args)
            elif method.lower() == "post":
                res = await client.post(url_path, params=query_args, json=body_data)
            elif method.lower() == "put":
                res = await client.put(url_path, params=query_args, json=body_data)
            elif method.lower() == "delete":
                res = await client.delete(url_path, params=query_args)
            else:
                return f"Unsupported HTTP method: {method}"
                
            # Parse and return response
            if res.status_code in (200, 201, 202, 207):
                try:
                    return res.json()
                except Exception:
                    return res.text
            elif res.status_code == 204:
                return "Operation completed successfully (No Content)."
            else:
                return f"Error {res.status_code}: {res.text}"
        except Exception as ex:
            logger.error(f"HTTP Request failed: {ex}")
            return f"HTTP Request failed: {ex}"
