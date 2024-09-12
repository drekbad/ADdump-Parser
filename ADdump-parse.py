import re
import argparse
from collections import defaultdict

def parse_html_file(input_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Regular expression to find groups (headers like "cn_XXXX")
    group_pattern = r'<thead><tr><td colspan="10" id="cn_(.*?)">(.*?)</td></tr></thead>'
    user_pattern = r'<tbody>.*?<tr><th>(.*?)</th>.*?<th>(.*?)</th>.*?<th>(.*?)</th>.*?</tr></tbody>'
    
    groups = re.findall(group_pattern, content)
    user_groups = defaultdict(list)

    # Loop through each group and find associated users
    for group_id, group_name in groups:
        user_table_pattern = rf'<thead><tr><td colspan="10" id="cn_{group_id}">.*?</thead>(.*?)</tbody>'
        user_table_match = re.search(user_table_pattern, content, re.DOTALL)
        if user_table_match:
            user_table = user_table_match.group(1)
            users = re.findall(user_pattern, user_table)
            # Extract "SAM Name" for each user
            for _, _, sam_name in users:
                user_groups[group_name].append(sam_name)

    return user_groups

def list_unique_groups(user_groups):
    print(f"All domain groups found: {len(user_groups)}")
    for group in user_groups.keys():
        print(f"- {group}")

def list_users_in_group(group_name, user_groups, output_file=None):
    users = user_groups.get(group_name, [])
    if users:
        unique_users = sorted(set(users))
        user_count = len(unique_users)
        output = [f"{group_name} has {user_count} unique users:"]
        output.extend(unique_users)

        if output_file:
            with open(output_file, 'w') as f:
                f.write("\n".join(output))
        else:
            print("\n".join(output))
    else:
        print(f"No users found for group: {group_name}")

def main():
    parser = argparse.ArgumentParser(description="Parse domain user groups and users from HTML.")
    parser.add_argument('-i', '--input', required=True, help='Input HTML file')
    parser.add_argument('-g', '--group', help='Group name to list users from')
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
