import json
import yaml
import re

"""
Little utility script to extract information from Grafana dashboard json.
"""

def slugify(s): return re.sub(r'[^a-z0-9-]', '', s.lower().replace(' ', '-'))

def extract_panel_info(dashboard_json):
    """
    Extracts title, targets.expr, and targets.legendFormat from dashboard panels

    Args:
        dashboard_json: Parsed JSON data from dashboard file

    Returns:
        list: List of dictionaries containing panel information
    """
    panels_info = []

    try:
        # Access the panels array from the dashboard
        if dashboard_json.get('dashboard', None) is not None:
            panels = dashboard_json['dashboard']['panels']
        else:
            # Or threat as nested panels
            panels = dashboard_json['panels']

        # Loop through each panel
        for panel in panels:
            panel_info = {
                'title': panel.get('title', ''),
                'expr': None,
                'legend': None
            }
            panel_info["slug"] = slugify(panel_info["title"])

            # Extract targets information if available
            if 'targets' in panel:
                for target in panel['targets']:
                    panel_info['expr'] = target.get('expr', ''),
                    panel_info['expr'] = ''.join(panel_info['expr'])
                    panel_info['legend'] = target.get('legendFormat', '').replace('{{','${').replace('}}', '}')
                panels_info.append(panel_info)
            elif 'panels' in panel:
                panels_info.extend(extract_panel_info(panel))
 
        return panels_info

    except KeyError as e:
        print(f"Error: Could not find key {str(e)} in dashboard JSON")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def read_and_extract_dashboard_info(filepath="dashboard.json"):
    """
    Reads dashboard JSON file and extracts panel information
    """
    try:
        with open(filepath, 'r') as file:
            dashboard_data = json.load(file)
            panels_info = extract_panel_info(dashboard_data)
            if panels_info is None:
                return None

            return panels_info

    except Exception as e:
        print(f"Error reading or processing file: {str(e)}")
        return None

def create_metric_binding(id, panel_info):
    return {
        'id': id,
        'name': panel_info["title"],
        'queries': [{
            'expression': panel_info['expr'],
            'alias': panel_info['legend']
        }],
        'scope': 'type in ("pod") and label = "kubevirt.io:virt-launcher"',
        'identifier': f"urn:stackpack:kubevirt:shared:metric-binding:vmi-{panel_info['slug']}",
        'unit': 'short',
        'chartType': 'line',
        'priority': 'high',
        'enabled': True,
        'layout': {
            'metricPerspective': {
                'tab': 'Virtualization',
                'section': 'Resource'
            },
            'componentSummary': {
                'weight': 3
            }
        },
        '_type': 'MetricBinding'
    }

def print_yaml(panel_infos):
    id = 100
    result = {
         "nodes": []
    }
    for p in panel_infos:
         result['nodes'].append(create_metric_binding(id * -1, p))
         id += 1
         
    print(yaml.dump(result, indent=2))

def print_summary(panel_infos):
    print('| Name | Promql |')
    print('| ---- | ------ |')
    for p in panel_infos:
        print(f"| {p['title']} | {p['expr']} |")
    
    
# Example usage
if __name__ == "__main__":
    panels_info = read_and_extract_dashboard_info(filepath='harvester-vminfo-grafana-dashboard.json')
    print(50*'-')
    print_summary(panels_info)
    print(50*'-')
    print_yaml(panels_info)
    print(50*'-')
