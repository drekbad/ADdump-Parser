import re
import argparse
from collections import defaultdict

def parse_html_file(input_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Pattern to find groups by display name (text right after id="cn_X")
    group_pattern = r'<thead><tr><td colspan="10" id="cn_(.*?)">(.*?)</td></tr></thead>'
    
    # Pattern to find users (extract third <td> in <tr> within <tbody> after the group's <thead>)
    user_table_pattern = r'<tbody>(.*?)</tbody>'
    user_row_pattern = r'<tr>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>'

    # Find all groups with their CN and display name
    groups = re.findall(group_pattern, content)
    user_groups = defaultdict(list)

    for group_id, group_name in groups:
        # Escape any special characters in the group ID to safely use in the regex
        group_escaped = re.escape(group_id)

        # Find the corresponding <tbody> section for the group
        user_table_search_pattern = rf'<thead><tr><td colspan="10" id="cn_{group_escaped}">.*?</thead>(.*?)</tbody>'
        user_table_match = re.search(user_table_search_pattern, content, re.DOTALL)
        
        if user_table_match:
            user_table = user_table_match.group(1)
            # Extract all user rows from this table, focusing on the third <td> (SAM Name)
            users = re.findall(user_row_pattern, user_table)
            
            for _, _, sam_name in users:
                user_groups[group_name].append(sam_name)

    return user_groups

def list_unique_groups(user_groups):
    unique_groups = sorted(set(user_groups.keys()))  # Remove duplicates and sort
    for group in unique_groups:
        print(group)
    
    # Print count at the end
    print(f"\nTotal groups found: {len(unique_groups)}")

def list_users_in_group(group_name, user_groups, output_file=None):
    # Find users in the specified group
    users = user_groups.get(group_name, [])
    
    if users:
        unique_users = sorted(set(users))  # Remove duplicates and sort users
        user_count = len(unique_users)
        output = unique_users

        if output_file:
            with open(output_file, 'w') as f:
                f.write("\n".join(output))
        else:
            print("\n".join(output))

        # Print count at the end
        print(f"\n{group_name} has {user_count} unique users.")
    else:
        print(f"No users found for group: {group_name}")

def main():
    parser = argparse.ArgumentParser(description="Parse domain user groups and users from HTML.")
    parser.add_argument('-i', '--input', required=True, help='Input HTML file')
    parser.add_argument('-g', '--group', help='Group name to list users from (e.g., "Domain Users")')
    parser.add_argument('-o', '--output', help='Output file for user list (optional)')
    args = parser.parse_args()

    # Parse the HTML file
    user_groups = parse_html_file(args.input)

    # If group is specified, list users in that group
    if args.group:
        list_users_in_group(args.group, user_groups, args.output)
    else:
        # List all unique groups if no group is specified
        list_unique_groups(user_groups)

if __name__ == "__main__":
    main()
