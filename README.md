# Expense-split-tracker
1. Problem Statement and Approach
Managing shared expenses in group settings—like trips or events—can quickly become messy. This Expense Split Tracker simplifies the process by:
• 	Allowing users to create groups and add members
• 	Supporting multiple split types: equal, exact amount, and percentage
• 	Tracking balances and enabling debt settlement
• 	Simplifying transactions to reduce the number of payments
Approach:
The project is implemented in pure Python using in-memory data structures like dictionaries and lists. It emphasizes clarity, modularity, and testability. All functionality is demonstrated through test cases in a single script—no external libraries or tools required.

2. Setup Instructions
Prerequisites
• 	Python 3.9 or higher
• 	A code editor or terminal to run  files
How to Run the Project
1. 	Clone or download the project folder
2. 	Navigate to the directory and run the script

3. 	Explore the built-in test cases
The script includes sample scenarios for:
• 	Equal split
• 	Exact amount split
• 	Percentage split
• 	Debt settlement
• 	Debt simplification

3. Explanations of Complex Logic
Expense Splitting
• 	Equal Split: Divides the total expense evenly among all members.
• 	Exact Amount Split: Assigns specific amounts to each user.
• 	Percentage Split: Calculates each user’s share based on given percentages.
Debt Simplification
We use a net balance algorithm:
• 	Compute each user’s net position (owed or receivable).
• 	Match payers with receivers to minimize the number of transactions.
Validations
• 	Prevent users from settling more than they owe
• 	Ensure expenses are added only for valid groups and users
• 	Handle edge cases like currency mismatches or missing data

4. Loom Video Demonstration
Watch the full walkthrough of the Expense Split Tracker in action:
https://www.loom.com/share/cbd0838511494449ab171e5a307a7299?sid=13d2df42-28ba-4d53-9d1c-1be0ccd02871
