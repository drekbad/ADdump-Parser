import re
import argparse
from collections import defaultdict

def parse_html_file(input_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Pattern to find groups by display name (text right after id="cn_X")
    group_pattern = r'<thead><tr><td colspan="10" id="cn_(.*?)">(.*?)</td></tr></thead>'
    
    # Pattern to find users (extract relevant <td> fields from <tr> within <tbody> after the group's <thead>)
    user_row_pattern = r'<tr>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>'

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
            # Extract all user rows from this table
            users = re.findall(user_row_pattern, user_table)
            
            for cn, name, sam_name, created_on, changed_on, last_logon, flags in users:
                user_groups[group_name].append((cn, sam_name, flags))

    return user_groups

def list_unique_groups(user_groups, sort_by_size=False):
    if sort_by_size:
        sorted_groups = sorted(user_groups.items(), key=lambda x: len(set(x[1])), reverse=True)
    else:
        sorted_groups = sorted(user_groups.items(), key=lambda x: x[0].lower())

    for group, users in sorted_groups:
        user_count = len(set(users))  # Unique users per group
        print(f"{group} - ({user_count})")
    
    # Print count at the end
    print(f"\nTotal groups found: {len(sorted_groups)}")

def list_users_in_group(group_name, user_groups, detailed=False, output_file=None):
    users = user_groups.get(group_name, [])
    
    if users:
        unique_users = sorted(set(users))  # Remove duplicates and sort users
        user_count = len(unique_users)

        if detailed:
            output = [f"{user[1]} ({user[0]}) - Flags: {user[2]}" for user in unique_users]
        else:
            output = [user[1] for user in unique_users]

        if output_file:
            with open(output_file, 'w') as f:
                f.write("\n".join(output))
        else:
            print("\n".join(output))

        # Print count at the top and bottom
        print(f"\n{group_name} has {user_count} unique users.")
    else:
        print(f"No users found for group: {group_name}")

def compare_sam_to_cn(sam_name, cn, formats):
    """
    Compares SAM name to CN based on the specified formats.
    Supported formats: 'first.last', 'fLast'.
    """
    cn_parts = cn.split()
    for fmt in formats:
        if fmt == 'first.last' and len(cn_parts) >= 2:
            expected_sam = '.'.join([cn_parts[0].lower(), cn_parts[-1].lower()])
        elif fmt == 'fLast' and len(cn_parts) >= 2:
            expected_sam = (cn_parts[0][0] + cn_parts[-1]).lower()
        else:
            continue
        
        if sam_name.lower() == expected_sam:
            return True
    return False

def check_users_for_format(user_groups, formats):
    flagged_accounts = []
    for group, users in user_groups.items():
        for cn, sam_name, flags in users:
            if not compare_sam_to_cn(sam_name, cn, formats):
                flagged_accounts.append((sam_name, cn, flags))
            elif 'DONT_EXPIRE_PASSWD' in flags:
                print(f"Potential standard account with non-expiring password: {sam_name} ({cn})")
    
    # Report flagged accounts
    if flagged_accounts:
        print(f"\nFlagged accounts that don't match specified formats:")
        for sam_name, cn, flags in flagged_accounts:
            print(f"{sam_name} ({cn}) - Flags: {flags}")

def main():
    parser = argparse.ArgumentParser(description="Parse domain user groups and users from HTML.")
    parser.add_argument('-i', '--input', required=True, help='Input HTML file')
    parser.add_argument('-g', '--group', help='Group name to list users from (e.g., "Domain Users")')
    parser.add_argument('-o', '--output', help='Output file for user list (optional)')
    parser.add_argument('--sort', action='store_true', help='Sort groups by number of users (largest to smallest)')
    parser.add_argument('--detailed', action='store_true', help='Display CN and flags for users in the specified group')
    
    # Naming format options (case-insensitive)
    parser.add_argument('--first-last', action='store_true', help='Expect SAM names in "first.last" format')
    parser.add_argument('--flast', action='store_true', help='Expect SAM names in "fLast" format')
    
    args = parser.parse_args()

    # Parse the HTML file
    user_groups = parse_html_file(args.input)

    # Gather expected formats
    formats = []
    if args.first_last:
        formats.append('first.last')
    if args.flast:
        formats.append('fLast')

    # If group is specified, list users in that group
    if args.group:
        list_users_in_group(args.group, user_groups, args.detailed, args.output)
    else:
        # List all unique groups if no group is specified, with optional sorting
        list_unique_groups(user_groups, args.sort)

    # If formats are provided, check SAM names against CN
    if formats:
        check_users_for_format(user_groups, formats)

if __name__ == "__main__":
    main()
