# Notion Integration Guide for Fitness Assessment App

## Table of Contents
1. [Overview](#overview)
2. [Python Libraries](#python-libraries)
3. [Authentication](#authentication)
4. [Database Operations](#database-operations)
5. [Page and Block Operations](#page-and-block-operations)
6. [Fitness App Integration](#fitness-app-integration)
7. [Best Practices](#best-practices)
8. [Use Cases](#use-cases)

## Overview

This guide provides comprehensive information for integrating Notion API into the fitness assessment application. Notion's API allows you to read and write data to Notion databases, making it ideal for syncing fitness data, creating dashboards, and managing client information.

## Python Libraries

### Official SDK (Recommended)
```bash
pip install notion-client
```

The official `notion-client` library is maintained by Notion and provides the most reliable and up-to-date API support.

### Alternative Libraries
- **notion-py**: Unofficial but feature-rich (may not support latest API features)
- **pynotion**: Lightweight alternative
- **notion-sdk-py**: Community-driven SDK

## Authentication

### Setting Up Internal Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Give it a name (e.g., "Fitness Assessment App")
4. Select the workspace
5. Copy the Internal Integration Token

### Environment Variable Setup
```python
import os
from notion_client import Client

# Store token in environment variable
notion = Client(auth=os.environ["NOTION_TOKEN"])
```

### Add to `.env` file:
```
NOTION_TOKEN=your-internal-integration-token
NOTION_FITNESS_DB_ID=your-database-id
```

### Sharing Databases with Integration
1. Open the Notion database you want to access
2. Click "Share" in the top right
3. Invite your integration by name
4. The integration now has access to that database

## Database Operations

### Query a Database
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = "your-database-id"

# Query all entries
response = notion.databases.query(database_id=database_id)

# Query with filters
response = notion.databases.query(
    database_id=database_id,
    filter={
        "property": "Status",
        "select": {
            "equals": "Active"
        }
    },
    sorts=[
        {
            "property": "Created",
            "direction": "descending"
        }
    ]
)

# Process results
for page in response["results"]:
    print(page["properties"])
```

### Get Database Schema
```python
# Retrieve database structure
database = notion.databases.retrieve(database_id=database_id)
print("Database properties:", database["properties"])
```

### Create a New Database
```python
new_db = notion.databases.create(
    parent={"page_id": parent_page_id},
    title=[
        {
            "type": "text",
            "text": {"content": "Fitness Assessments"}
        }
    ],
    properties={
        "Client Name": {"title": {}},
        "Assessment Date": {"date": {}},
        "Weight": {"number": {"format": "number"}},
        "Body Fat %": {"number": {"format": "percent"}},
        "Fitness Score": {"number": {"format": "number"}}
    }
)
```

## Page and Block Operations

### Retrieve a Page
```python
page_id = "your-page-id"
page = notion.pages.retrieve(page_id=page_id)

# Access page properties
title = page["properties"]["Name"]["title"][0]["text"]["content"]
```

### Create a New Page (Database Entry)
```python
new_page = notion.pages.create(
    parent={"database_id": database_id},
    properties={
        "Name": {
            "title": [
                {"text": {"content": "John Doe - Assessment"}}
            ]
        },
        "Date": {
            "date": {"start": "2024-01-15"}
        },
        "Score": {
            "number": 85
        }
    }
)
```

### Fetch Page Content (Blocks)
```python
blocks = notion.blocks.children.list(block_id=page_id)

for block in blocks["results"]:
    block_type = block["type"]
    
    if block_type == "paragraph":
        text = block["paragraph"]["rich_text"][0]["text"]["content"]
        print(f"Paragraph: {text}")
    elif block_type == "heading_1":
        text = block["heading_1"]["rich_text"][0]["text"]["content"]
        print(f"Heading: {text}")
```

## Fitness App Integration

### Complete Integration Service
```python
# src/services/notion_service.py
import os
from datetime import datetime
from typing import List, Dict, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

class NotionFitnessIntegration:
    def __init__(self, token: str = None):
        self.notion = Client(auth=token or os.environ["NOTION_TOKEN"])
        self.fitness_db_id = os.environ.get("NOTION_FITNESS_DB_ID")
        
    def create_fitness_database(self, parent_page_id: str) -> Dict:
        """Create a comprehensive fitness tracking database"""
        return self.notion.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Fitness Assessments"}}],
            properties={
                "Client Name": {"title": {}},
                "Assessment Date": {"date": {}},
                "Age": {"number": {"format": "number"}},
                "Weight (kg)": {"number": {"format": "number"}},
                "Height (cm)": {"number": {"format": "number"}},
                "Body Fat %": {"number": {"format": "percent"}},
                "Muscle Mass (kg)": {"number": {"format": "number"}},
                "BMI": {"number": {"format": "number"}},
                "Waist-Hip Ratio": {"number": {"format": "number"}},
                "VO2 Max": {"number": {"format": "number"}},
                "Flexibility Score": {"number": {"format": "number"}},
                "Overall Fitness Score": {"number": {"format": "number"}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Excellent", "color": "green"},
                            {"name": "Good", "color": "blue"},
                            {"name": "Fair", "color": "yellow"},
                            {"name": "Needs Improvement", "color": "red"}
                        ]
                    }
                },
                "Goals": {
                    "multi_select": {
                        "options": [
                            {"name": "Weight Loss", "color": "pink"},
                            {"name": "Muscle Gain", "color": "purple"},
                            {"name": "Endurance", "color": "orange"},
                            {"name": "Flexibility", "color": "gray"},
                            {"name": "General Fitness", "color": "blue"}
                        ]
                    }
                },
                "Notes": {"rich_text": {}},
                "Recommendations": {"rich_text": {}}
            }
        )
    
    def sync_assessment_to_notion(self, assessment_data: Dict) -> Dict:
        """Sync a fitness assessment from your app to Notion"""
        try:
            properties = {
                "Client Name": {
                    "title": [{"text": {"content": assessment_data["client_name"]}}]
                },
                "Assessment Date": {
                    "date": {"start": assessment_data["date"]}
                },
                "Age": {"number": assessment_data.get("age", 0)},
                "Weight (kg)": {"number": assessment_data.get("weight", 0)},
                "Height (cm)": {"number": assessment_data.get("height", 0)},
                "Body Fat %": {"number": assessment_data.get("body_fat_percentage", 0) / 100},
                "Muscle Mass (kg)": {"number": assessment_data.get("muscle_mass", 0)},
                "BMI": {"number": assessment_data.get("bmi", 0)},
                "Overall Fitness Score": {"number": assessment_data.get("fitness_score", 0)},
                "Status": {
                    "select": {"name": self._get_status(assessment_data.get("fitness_score", 0))}
                }
            }
            
            # Add optional fields if present
            if "waist_hip_ratio" in assessment_data:
                properties["Waist-Hip Ratio"] = {"number": assessment_data["waist_hip_ratio"]}
            
            if "vo2_max" in assessment_data:
                properties["VO2 Max"] = {"number": assessment_data["vo2_max"]}
            
            if "flexibility_score" in assessment_data:
                properties["Flexibility Score"] = {"number": assessment_data["flexibility_score"]}
            
            if "notes" in assessment_data:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": assessment_data["notes"]}}]
                }
            
            if "recommendations" in assessment_data:
                properties["Recommendations"] = {
                    "rich_text": [{"text": {"content": assessment_data["recommendations"]}}]
                }
            
            return self.notion.pages.create(
                parent={"database_id": self.fitness_db_id},
                properties=properties
            )
            
        except APIResponseError as e:
            print(f"Error syncing to Notion: {e}")
            raise
    
    def import_assessments_from_notion(self, 
                                     client_name: Optional[str] = None,
                                     start_date: Optional[str] = None) -> List[Dict]:
        """Import fitness assessments from Notion"""
        filters = []
        
        if client_name:
            filters.append({
                "property": "Client Name",
                "title": {"contains": client_name}
            })
        
        if start_date:
            filters.append({
                "property": "Assessment Date",
                "date": {"after": start_date}
            })
        
        query_params = {
            "database_id": self.fitness_db_id,
            "sorts": [{"property": "Assessment Date", "direction": "descending"}]
        }
        
        if filters:
            if len(filters) > 1:
                query_params["filter"] = {"and": filters}
            else:
                query_params["filter"] = filters[0]
        
        response = self.notion.databases.query(**query_params)
        
        assessments = []
        for page in response["results"]:
            props = page["properties"]
            
            assessment = {
                "notion_page_id": page["id"],
                "client_name": self._get_text_from_property(props.get("Client Name", {})),
                "date": props.get("Assessment Date", {}).get("date", {}).get("start", ""),
                "age": props.get("Age", {}).get("number", 0),
                "weight": props.get("Weight (kg)", {}).get("number", 0),
                "height": props.get("Height (cm)", {}).get("number", 0),
                "body_fat_percentage": props.get("Body Fat %", {}).get("number", 0) * 100,
                "muscle_mass": props.get("Muscle Mass (kg)", {}).get("number", 0),
                "bmi": props.get("BMI", {}).get("number", 0),
                "fitness_score": props.get("Overall Fitness Score", {}).get("number", 0),
                "status": props.get("Status", {}).get("select", {}).get("name", ""),
                "waist_hip_ratio": props.get("Waist-Hip Ratio", {}).get("number", 0),
                "vo2_max": props.get("VO2 Max", {}).get("number", 0),
                "flexibility_score": props.get("Flexibility Score", {}).get("number", 0),
                "notes": self._get_text_from_property(props.get("Notes", {})),
                "recommendations": self._get_text_from_property(props.get("Recommendations", {}))
            }
            
            assessments.append(assessment)
        
        return assessments
    
    def update_assessment_in_notion(self, page_id: str, updates: Dict) -> Dict:
        """Update an existing assessment in Notion"""
        properties = {}
        
        # Map updates to Notion properties
        field_mapping = {
            "weight": ("Weight (kg)", "number", 1),
            "body_fat_percentage": ("Body Fat %", "number", 0.01),
            "muscle_mass": ("Muscle Mass (kg)", "number", 1),
            "fitness_score": ("Overall Fitness Score", "number", 1),
            "notes": ("Notes", "rich_text", None),
            "recommendations": ("Recommendations", "rich_text", None)
        }
        
        for key, value in updates.items():
            if key in field_mapping:
                notion_prop, prop_type, multiplier = field_mapping[key]
                
                if prop_type == "number":
                    properties[notion_prop] = {"number": value * multiplier if multiplier else value}
                elif prop_type == "rich_text":
                    properties[notion_prop] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }
        
        if "fitness_score" in updates:
            properties["Status"] = {
                "select": {"name": self._get_status(updates["fitness_score"])}
            }
        
        return self.notion.pages.update(page_id=page_id, properties=properties)
    
    def get_client_progress(self, client_name: str, limit: int = 10) -> List[Dict]:
        """Get fitness progress trends for a specific client"""
        assessments = self.import_assessments_from_notion(client_name=client_name)
        
        # Return only the required fields for trend analysis
        trends = []
        for assessment in assessments[:limit]:
            trends.append({
                "date": assessment["date"],
                "weight": assessment["weight"],
                "body_fat_percentage": assessment["body_fat_percentage"],
                "muscle_mass": assessment["muscle_mass"],
                "fitness_score": assessment["fitness_score"],
                "bmi": assessment["bmi"]
            })
        
        return trends
    
    def _get_status(self, score: float) -> str:
        """Determine status based on fitness score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_text_from_property(self, prop: Dict) -> str:
        """Extract text from various Notion property types"""
        if "title" in prop and prop["title"]:
            return prop["title"][0]["text"]["content"]
        elif "rich_text" in prop and prop["rich_text"]:
            return prop["rich_text"][0]["text"]["content"]
        return ""
```

### Integration with Existing Models
```python
# src/services/notion_sync_service.py
from typing import Optional
from datetime import datetime
from src.core.models import FitnessAssessment, Client
from src.services.notion_service import NotionFitnessIntegration

class NotionSyncService:
    def __init__(self):
        self.notion = NotionFitnessIntegration()
    
    def sync_assessment(self, assessment: FitnessAssessment, client: Client) -> Optional[str]:
        """Sync a FitnessAssessment model to Notion"""
        assessment_data = {
            "client_name": f"{client.first_name} {client.last_name}",
            "date": assessment.assessment_date.isoformat(),
            "age": client.age,
            "weight": assessment.weight,
            "height": assessment.height,
            "body_fat_percentage": assessment.body_fat_percentage,
            "muscle_mass": assessment.muscle_mass,
            "bmi": assessment.bmi,
            "waist_hip_ratio": assessment.waist_hip_ratio,
            "vo2_max": assessment.vo2_max,
            "flexibility_score": assessment.flexibility_score,
            "fitness_score": assessment.overall_score,
            "notes": assessment.notes or "",
            "recommendations": self._generate_recommendations(assessment)
        }
        
        try:
            result = self.notion.sync_assessment_to_notion(assessment_data)
            return result["id"]
        except Exception as e:
            print(f"Failed to sync assessment: {e}")
            return None
    
    def import_to_database(self, client_name: Optional[str] = None):
        """Import assessments from Notion to local database"""
        assessments = self.notion.import_assessments_from_notion(client_name=client_name)
        
        # Convert to your model format and save
        for assessment_data in assessments:
            # Implementation depends on your database service
            pass
    
    def _generate_recommendations(self, assessment: FitnessAssessment) -> str:
        """Generate recommendations based on assessment"""
        recommendations = []
        
        if assessment.body_fat_percentage > 25:
            recommendations.append("Consider incorporating more cardiovascular exercise")
        
        if assessment.muscle_mass < 30:
            recommendations.append("Focus on strength training exercises")
        
        if assessment.flexibility_score < 7:
            recommendations.append("Add stretching or yoga to your routine")
        
        return "; ".join(recommendations)
```

## Best Practices

### 1. Error Handling
```python
from notion_client import APIResponseError

try:
    response = notion.databases.query(database_id=database_id)
except APIResponseError as error:
    if error.code == "object_not_found":
        print("Database not found. Check the ID and permissions.")
    elif error.code == "unauthorized":
        print("Integration doesn't have access to this database.")
    else:
        print(f"API error: {error.code} - {error.message}")
```

### 2. Rate Limiting
Notion API has rate limits. Implement delays between requests:

```python
import time
from typing import List

def batch_sync_with_rate_limit(items: List, delay: float = 0.35):
    """Respect Notion API rate limits"""
    synced_items = []
    
    for i, item in enumerate(items):
        try:
            result = sync_item_to_notion(item)
            synced_items.append(result)
            
            # Add delay between requests (except for the last one)
            if i < len(items) - 1:
                time.sleep(delay)
                
        except APIResponseError as e:
            if e.code == "rate_limited":
                # Wait longer and retry
                time.sleep(5)
                result = sync_item_to_notion(item)
                synced_items.append(result)
            else:
                print(f"Failed to sync {item}: {e}")
                continue
    
    return synced_items
```

### 3. Configuration Management
```python
# config/notion_config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class NotionConfig:
    token: str
    fitness_database_id: str
    workout_database_id: Optional[str] = None
    nutrition_database_id: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            token=os.getenv("NOTION_TOKEN", ""),
            fitness_database_id=os.getenv("NOTION_FITNESS_DB_ID", ""),
            workout_database_id=os.getenv("NOTION_WORKOUT_DB_ID"),
            nutrition_database_id=os.getenv("NOTION_NUTRITION_DB_ID")
        )
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.token:
            raise ValueError("NOTION_TOKEN is required")
        if not self.fitness_database_id:
            raise ValueError("NOTION_FITNESS_DB_ID is required")
        return True
```

### 4. Caching
Implement caching to reduce API calls:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedNotionClient:
    def __init__(self, notion_client):
        self.notion = notion_client
        self._cache = {}
        self._cache_expiry = {}
    
    def get_database(self, database_id: str, cache_duration: int = 300):
        """Get database with caching (default 5 minutes)"""
        cache_key = f"db_{database_id}"
        
        # Check if cached and not expired
        if cache_key in self._cache:
            if datetime.now() < self._cache_expiry[cache_key]:
                return self._cache[cache_key]
        
        # Fetch from API
        result = self.notion.databases.retrieve(database_id=database_id)
        
        # Cache the result
        self._cache[cache_key] = result
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=cache_duration)
        
        return result
```

### 5. Pagination
Handle large datasets with pagination:

```python
def get_all_assessments(self, database_id: str) -> List[Dict]:
    """Fetch all assessments handling pagination"""
    all_results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        if start_cursor:
            response = self.notion.databases.query(
                database_id=database_id,
                start_cursor=start_cursor
            )
        else:
            response = self.notion.databases.query(database_id=database_id)
        
        all_results.extend(response["results"])
        has_more = response["has_more"]
        start_cursor = response.get("next_cursor")
    
    return all_results
```

## Use Cases

### 1. Client Progress Dashboard
Create a Notion dashboard that automatically updates with client progress:

```python
def create_progress_dashboard(client_name: str):
    """Create a comprehensive progress view in Notion"""
    # Get historical data
    progress = notion_service.get_client_progress(client_name, limit=12)
    
    # Create a new page with charts and insights
    dashboard_properties = {
        "title": f"{client_name} - Progress Dashboard",
        "last_updated": datetime.now().isoformat(),
        "total_assessments": len(progress),
        "average_score": sum(p["fitness_score"] for p in progress) / len(progress)
    }
    
    # Add trend analysis
    if len(progress) >= 2:
        latest = progress[0]
        previous = progress[1]
        
        dashboard_properties["weight_change"] = latest["weight"] - previous["weight"]
        dashboard_properties["body_fat_change"] = latest["body_fat_percentage"] - previous["body_fat_percentage"]
        dashboard_properties["muscle_change"] = latest["muscle_mass"] - previous["muscle_mass"]
```

### 2. Automated Reporting
Generate weekly/monthly reports in Notion:

```python
def generate_weekly_report():
    """Create a weekly summary in Notion"""
    # Get assessments from the past week
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    assessments = notion_service.import_assessments_from_notion(start_date=start_date)
    
    # Create summary statistics
    summary = {
        "total_assessments": len(assessments),
        "average_fitness_score": sum(a["fitness_score"] for a in assessments) / len(assessments),
        "clients_assessed": len(set(a["client_name"] for a in assessments))
    }
    
    # Create report page in Notion
    # ...
```

### 3. Goal Tracking Integration
Track fitness goals alongside assessments:

```python
def create_goal_tracker(client_name: str, goals: List[Dict]):
    """Create a goal tracking system in Notion"""
    goal_properties = {
        "Client": client_name,
        "Goals": [
            {
                "goal": goal["description"],
                "target_date": goal["target_date"],
                "metric": goal["metric"],
                "target_value": goal["target_value"],
                "current_value": goal["current_value"]
            }
            for goal in goals
        ]
    }
    
    # Create in Notion and link to assessments
    # ...
```

### 4. Nutrition and Workout Integration
Extend the system to track nutrition and workouts:

```python
class NotionFitnessEcosystem:
    """Complete fitness tracking ecosystem in Notion"""
    
    def __init__(self):
        self.notion = Client(auth=os.environ["NOTION_TOKEN"])
        self.databases = {
            "assessments": os.environ["NOTION_FITNESS_DB_ID"],
            "workouts": os.environ["NOTION_WORKOUT_DB_ID"],
            "nutrition": os.environ["NOTION_NUTRITION_DB_ID"],
            "goals": os.environ["NOTION_GOALS_DB_ID"]
        }
    
    def create_complete_profile(self, client_data: Dict):
        """Create a complete fitness profile with all related data"""
        # Create main client page
        # Link assessments, workouts, nutrition, and goals
        # Set up automated relations between databases
        pass
```

### 5. Team Collaboration
Enable trainers to collaborate through Notion:

```python
def share_client_with_trainer(client_page_id: str, trainer_email: str):
    """Share client data with another trainer"""
    # Note: Sharing is done through Notion UI, but you can:
    # 1. Add trainer notes section
    # 2. Create trainer-specific views
    # 3. Set up notification system for updates
    
    trainer_section = {
        "Trainer Notes": {"rich_text": []},
        "Assigned Trainer": {"email": trainer_email},
        "Last Review Date": {"date": {"start": datetime.now().isoformat()}}
    }
    
    # Update the page with trainer information
    # ...
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Errors**
   - Verify your integration token is correct
   - Ensure the integration has been added to the database/page
   - Check workspace permissions

2. **Rate Limiting**
   - Implement exponential backoff
   - Cache frequently accessed data
   - Batch operations when possible

3. **Data Type Mismatches**
   - Ensure number properties are actually numbers (not strings)
   - Date formats must be ISO 8601
   - Percentages in Notion are 0-1, not 0-100

4. **Missing Properties**
   - Always check if properties exist before accessing
   - Use `.get()` method with defaults
   - Validate data before sending to Notion

## Additional Resources

- [Notion API Documentation](https://developers.notion.com/)
- [notion-client Python SDK](https://github.com/ramnes/notion-sdk-py)
- [Notion API Postman Collection](https://www.postman.com/notionhq/workspace/notion-s-api-workspace/)
- [Notion API Changelog](https://developers.notion.com/changelog)

## Security Considerations

1. **Never commit tokens to version control**
   ```bash
   # .gitignore
   .env
   *.env
   ```

2. **Use environment variables for all sensitive data**

3. **Implement proper access controls**
   - Only share necessary databases with integration
   - Use read-only access where possible
   - Regularly audit integration permissions

4. **Data Privacy**
   - Consider GDPR/HIPAA compliance for health data
   - Implement data retention policies
   - Allow users to request data deletion

This guide should provide a comprehensive foundation for integrating Notion with your fitness assessment application. The modular approach allows you to implement features incrementally based on your needs.