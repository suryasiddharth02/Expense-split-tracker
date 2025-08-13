from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import uuid

@dataclass
class User:
    id: str
    name: str
    currency: str = "USD"
    balance: float = 0.0

@dataclass
class Expense:
    id: str
    description: str
    amount: float
    currency: str
    split_type: str
    shares: Dict[str, float]
    paid_by: Optional[str] = None

@dataclass
class Transaction:
    id: str
    from_user: Optional[str]
    to_user: Optional[str]
    amount: float
    currency: str
    note: str = ""

class Group:
    def __init__(self, name: str, currency: str = "USD"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.currency = currency
        self.users: Dict[str, User] = {}
        self.expenses: List[Expense] = []
        self.transactions: List[Transaction] = []
    
    def add_user(self, name: str, currency: Optional[str] = None) -> User:
        currency = currency or self.currency
        user = User(id=str(uuid.uuid4()), name=name, currency=currency, balance=0.0)
        self.users[user.id] = user
        return user
    
    def _validate_currency(self, currency: str):
        if currency != self.currency:
            raise ValueError(f"Currency mismatch: group currency is {self.currency}, expense is {currency}.")
    
    def add_expense(self, amount: float, split_type: str, users: Optional[List[str]] = None,
                    exact_amounts: Optional[Dict[str, float]] = None,
                    percentages: Optional[Dict[str, float]] = None,
                    description: str = "", paid_by: Optional[str] = None,
                    currency: Optional[str] = None) -> Expense:
        currency = currency or self.currency
        self._validate_currency(currency)
        split_type = split_type.lower()
        shares: Dict[str, float] = {}
        
        if split_type == "equal":
            if not users:
                raise ValueError("Equal split requires a list of users.")
            share = round(amount / len(users), 2)
            for i, uid in enumerate(users):
                shares[uid] = share
            total_assigned = sum(shares.values())
            if total_assigned != round(amount, 2):
                diff = round(amount - total_assigned, 2)
                shares[users[-1]] += diff
        
        elif split_type == "exact":
            if not exact_amounts:
                raise ValueError("Exact split requires exact_amounts mapping.")
            total = round(sum(exact_amounts.values()), 2)
            if abs(total - amount) > 1e-9:
                raise ValueError(f"Exact amounts sum to {total}, which does not equal expense amount {amount}.")
            shares = {uid: round(val, 2) for uid, val in exact_amounts.items()}
        
        elif split_type == "percentage":
            if not percentages:
                raise ValueError("Percentage split requires percentages mapping.")
            total_percent = round(sum(percentages.values()), 2)
            if abs(total_percent - 100.0) > 1e-9:
                raise ValueError(f"Percentages must sum to 100, got {total_percent}.")
            for uid, pct in percentages.items():
                shares[uid] = round(amount * (pct / 100.0), 2)
            total_assigned = sum(shares.values())
            if total_assigned != round(amount, 2):
                diff = round(amount - total_assigned, 2)
                last_uid = list(percentages.keys())[-1]
                shares[last_uid] += diff
        else:
            raise ValueError("Unsupported split_type. Use 'equal', 'exact', or 'percentage'.")
        
        expense = Expense(id=str(uuid.uuid4()), description=description, amount=round(amount, 2),
                          currency=currency, split_type=split_type, shares=shares, paid_by=paid_by)
        self.expenses.append(expense)
        
        for uid, share_amt in shares.items():
            if uid not in self.users:
                raise ValueError(f"User id {uid} not in group.")
            self.users[uid].balance = round(self.users[uid].balance + share_amt, 2)
        
        if paid_by:
            if paid_by not in self.users:
                raise ValueError(f"Payer {paid_by} not a member of the group.")
            self.users[paid_by].balance = round(self.users[paid_by].balance - amount, 2)
        
        tx = Transaction(id=str(uuid.uuid4()), from_user=None, to_user=None, amount=round(amount,2), currency=currency, note=f"Expense: {description} ({split_type})")
        self.transactions.append(tx)
        
        return expense
    
    def settle_debt(self, user_id: str, amount: float, to_user_id: Optional[str] = None):
        if user_id not in self.users:
            raise ValueError("User not in group.")
        user = self.users[user_id]
        amount = round(amount, 2)
        if amount < 0:
            raise ValueError("Amount must be non-negative.")
        if user.balance > 0 and amount > user.balance + 1e-9:
            raise ValueError(f"Cannot settle more than owed. User owes {user.balance}, tried to settle {amount}.")
        if user.balance <= 0 and amount > 0:
            raise ValueError(f"User does not owe anything (balance={user.balance}); cannot settle a positive amount.")
        user.balance = round(user.balance - amount, 2)
        tx = Transaction(id=str(uuid.uuid4()), from_user=user_id, to_user=to_user_id, amount=amount, currency=self.currency, note="Settlement")
        self.transactions.append(tx)
        return tx
    
    def get_balances(self) -> Dict[str, float]:
        return {uid: round(u.balance, 2) for uid, u in self.users.items()}
    
    def simplify_debts(self) -> List[Transaction]:
        debtors: List[Tuple[str, float]] = []
        creditors: List[Tuple[str, float]] = []
        for uid, user in self.users.items():
            bal = round(user.balance, 2)
            if bal > 0:
                debtors.append([uid, bal])
            elif bal < 0:
                creditors.append([uid, -bal])
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
        settlements: List[Transaction] = []
        i = 0
        j = 0
        while i < len(debtors) and j < len(creditors):
            debtor_id, owe_amt = debtors[i]
            creditor_id, recv_amt = creditors[j]
            transfer = round(min(owe_amt, recv_amt), 2)
            tx = Transaction(id=str(uuid.uuid4()), from_user=debtor_id, to_user=creditor_id, amount=transfer, currency=self.currency, note="Simplified settlement")
            settlements.append(tx)
            self.transactions.append(tx)
            debtors[i][1] = round(debtors[i][1] - transfer, 2)
            creditors[j][1] = round(creditors[j][1] - transfer, 2)
            self.users[debtor_id].balance = round(self.users[debtor_id].balance - transfer, 2)
            self.users[creditor_id].balance = round(self.users[creditor_id].balance + transfer, 2)
            if abs(debtors[i][1]) < 1e-9:
                i += 1
            if abs(creditors[j][1]) < 1e-9:
                j += 1
        return settlements
    
    def view_transaction_history(self) -> List[Transaction]:
        return self.transactions


# -------------------- Helper functions --------------------

def create_group(name: str, currency: str = "USD") -> Group:
    return Group(name=name, currency=currency)

def add_user(group: Group, name: str, currency: Optional[str] = None) -> User:
    return group.add_user(name=name, currency=currency)

def add_expense(group: Group, amount: float, split_type: str, users: Optional[List[User]] = None,
                exact_amounts: Optional[Dict[User, float]] = None,
                percentages: Optional[Dict[User, float]] = None,
                description: str = "", paid_by: Optional[User] = None):
    user_ids = [u.id for u in users] if users else None
    exact_map = {u.id: v for u, v in exact_amounts.items()} if exact_amounts else None
    pct_map = {u.id: v for u, v in percentages.items()} if percentages else None
    payer_id = paid_by.id if paid_by else None
    return group.add_expense(amount=amount, split_type=split_type, users=user_ids, exact_amounts=exact_map, percentages=pct_map, description=description, paid_by=payer_id)

def settle_debt(group: Group, user: User, amount: float, to_user: Optional[User] = None):
    to_id = to_user.id if to_user else None
    return group.settle_debt(user.id, amount, to_user_id=to_id)

def simplify_debts(group: Group):
    return group.simplify_debts()


# -------------------- Tests --------------------
def run_tests():
    print("Running test_equal_split...")
    group = create_group("Trip to Paris")
    user1 = add_user(group, "User1")
    user2 = add_user(group, "User2")
    user3 = add_user(group, "User3")
    expense = add_expense(group, amount=90, split_type="equal", users=[user1, user2, user3])
    balances = group.get_balances()
    assert round(balances[user1.id],2) == 30.00
    assert round(balances[user2.id],2) == 30.00
    assert round(balances[user3.id],2) == 30.00
    print("test_equal_split passed. Balances:", {group.users[k].name: v for k,v in balances.items()})
    
    print("Running test_exact_amount_split...")
    group = create_group("Dinner")
    user1 = add_user(group, "User1")
    user2 = add_user(group, "User2")
    expense = group.add_expense(amount=100, split_type="exact", exact_amounts={user1.id:70, user2.id:30})
    balances = group.get_balances()
    assert round(balances[user1.id],2) == 70.00
    assert round(balances[user2.id],2) == 30.00
    print("test_exact_amount_split passed. Balances:", {group.users[k].name: v for k,v in balances.items()})
    
    print("Running test_percentage_split...")
    group = create_group("Shopping Trip")
    user1 = add_user(group, "User1")
    user2 = add_user(group, "User2")
    expense = group.add_expense(amount=200, split_type="percentage", percentages={user1.id:60, user2.id:40})
    balances = group.get_balances()
    assert round(balances[user1.id],2) == 120.00
    assert round(balances[user2.id],2) == 80.00
    print("test_percentage_split passed. Balances:", {group.users[k].name: v for k,v in balances.items()})
    
    print("Running test_settling_debt...")
    group = create_group("Trip to Goa")
    user1 = add_user(group, "User1")
    expense = group.add_expense(amount=50, split_type="equal", users=[user1.id])
    tx = group.settle_debt(user1.id, 50)
    balances = group.get_balances()
    assert round(balances[user1.id],2) == 0.00
    print("test_settling_debt passed. Balances:", {group.users[k].name: v for k,v in balances.items()})
    
    print("Running test_simplify_debts...")
    group = create_group("Trip to Goa - simplify")
    user1 = add_user(group, "User1")
    user2 = add_user(group, "User2")
    group.add_expense(amount=30, split_type="equal", users=[user1.id, user2.id], paid_by=user2.id, description="Expense1")
    group.add_expense(amount=20, split_type="equal", users=[user1.id, user2.id], paid_by=user1.id, description="Expense2")
    balances_before = group.get_balances()
    print("Balances before simplification:", {group.users[k].name: v for k,v in balances_before.items()})
    settlements = group.simplify_debts()
    balances_after = group.get_balances()
    print("Settlements suggested:")
    for s in settlements:
        print(f"  {group.users[s.from_user].name} -> {group.users[s.to_user].name}: {s.amount} {s.currency}")
    print("Balances after simplification:", {group.users[k].name: v for k,v in balances_after.items()})
    assert abs(balances_after[user1.id]) < 1e-9
    assert abs(balances_after[user2.id]) < 1e-9
    print("test_simplify_debts passed.")
    
    print("\nAll tests passed.")
    
if __name__ == "__main__":
    run_tests()
