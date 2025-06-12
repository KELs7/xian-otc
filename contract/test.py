import unittest
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal as Decimal

# Define fixed date for deterministic tests
TEST_DATETIME = Datetime(year=2024, month=6, day=20, hour=10, minute=0, second=0)

# Add a slightly different time for the second call
TEST_DATETIME_PLUS_1SEC = Datetime(year=2024, month=6, day=20, hour=10, minute=0, second=1)

TEST_DATETIME_LIST_EXPLOIT = Datetime(year=2024, month=6, day=21, hour=10, minute=0, second=0)

class TestOtcContract(unittest.TestCase):
    # Class variables for easier access in tests
    otc_owner_vk = "otc_owner_wallet"
    maker_vk = "maker_wallet"
    taker_vk = "taker_wallet"
    other_vk = "other_wallet"
    otc_contract_name = "con_otc"
    token_a_name = "con_token_a"
    token_b_name = "con_token_b"
    token_c_name = "con_token_c_conceptual" # ADD THIS LINE
    exploit_contract_name = "con_breakotc" # Name for the malicious contract
    attacker_vk = "attacker_wallet"
    vulnerable_otc_name_for_exploit = "con_otc_vulnerable"
    safeguarded_otc_name_for_exploit = "con_otc_v3"

    initial_balance = Decimal("10000.0")
    default_fee_percent = Decimal("0.5")

    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()

        # Deploy OTC Contract
        with open("con_otc_v3.py") as f:
            code = f.read()
            self.client.submit(code, name=self.otc_contract_name, signer=self.otc_owner_vk)
        self.otc_contract = self.client.get_contract(self.otc_contract_name)

        # Deploy Mock Tokens
        self.token_a = self._deploy_mock_token(self.token_a_name, "TokenA", "TKA")
        self.token_b = self._deploy_mock_token(self.token_b_name, "TokenB", "TKB")

        # Fund Accounts
        self._fund_account(self.token_a, self.maker_vk)
        self._fund_account(self.token_b, self.taker_vk)
        # self._fund_account(self.token_a, self.attacker_vk) # Fund owner for some tests if needed
        self._fund_account(self.token_b, self.otc_owner_vk)

        # Set environment for predictable tests
        self.environment = {"chain_id": "test-chain"}

    def tearDown(self):
        self.client.flush()


    def _deploy_mock_token(self, name: str, token_name: str, token_symbol: str):
        # ... (no changes needed here) ...
        with open("con_token.py") as f:
            code = f.read()
            self.client.submit(
                code,
                name=name,
                constructor_args={
                    "vk": self.otc_owner_vk,
                    "name": token_name,
                    "symbol": token_symbol,
                },
                signer=self.otc_owner_vk
            )
        return self.client.get_contract(name)

    def _deploy_contract_from_file(self, file_path: str, contract_name: str, signer_vk: str, constructor_args: dict = None):
        with open(file_path) as f:
            code = f.read()
            self.client.submit(
                code,
                name=contract_name,
                signer=signer_vk,
                constructor_args=constructor_args if constructor_args else {}
            )
        return self.client.get_contract(contract_name)

    def _fund_account(self, token_contract, account_vk: str, amount: Decimal = None):
        if amount is None:
            amount = self.initial_balance
        # Pass Decimal directly
        token_contract.transfer(
            amount=amount,
            to=account_vk,
            signer=self.otc_owner_vk,
        )

    def _approve_transfer(self, token_contract, vk: str, spender_vk: str, amount: Decimal):
        # Pass Decimal directly
        token_contract.approve(amount=amount, to=spender_vk, signer=vk)
        # FIX: Compare ContractingDecimal with Decimal directly
        self.assertEqual(token_contract.balances[vk, spender_vk], amount)

    # Helper to get balance - returns ContractingDecimal or Decimal(0)
    def _get_balance_contracting_or_zero(self, token_contract, vk: str):
        balance = token_contract.balance_of(address=vk)
        # Return ContractingDecimal or standard Decimal(0.0) if None
        return balance if balance is not None else Decimal("0.0")

    # --- Test Cases ---

    def test_01_init_state(self):
        self.assertEqual(self.otc_contract.owner.get(), self.otc_owner_vk)
        # FIX: Compare ContractingDecimal with Decimal directly
        self.assertEqual(self.otc_contract.fee.get(), self.default_fee_percent)

    def test_02_list_offer_happy_path(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        # Fee calculation remains standard Decimal math
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        required_approval = offer_amount + maker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, required_approval)
        # Get initial balances (may be ContractingDecimal)
        maker_initial_balance = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        contract_initial_balance = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)

        environment = {**self.environment, "now": TEST_DATETIME}
        # Pass standard Decimals to the contract call
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk,
            environment=environment,
            offer_token=self.token_a_name,
            offer_amount=offer_amount,
            take_token=self.token_b_name,
            take_amount=take_amount,
        )

        self.assertIsNotNone(listing_id)
        offer = self.otc_contract.otc_listing[listing_id]
        self.assertIsNotNone(offer)
        self.assertEqual(offer["maker"], self.maker_vk)
        self.assertEqual(offer["offer_token"], self.token_a_name)
        # FIX: Compare ContractingDecimal/Decimal from state with Decimal directly
        self.assertEqual(offer["offer_amount"], offer_amount)
        self.assertEqual(offer["take_token"], self.token_b_name)
        self.assertEqual(offer["take_amount"], take_amount)
        self.assertEqual(offer["fee"], self.default_fee_percent) # Compare fee
        self.assertEqual(offer["status"], "OPEN")
        self.assertIsNone(offer["taker"])

        # Verify token balances by comparing ContractingDecimal result with Decimal math
        self.assertEqual(
            self._get_balance_contracting_or_zero(self.token_a, self.maker_vk),
            maker_initial_balance - required_approval,
        )
        self.assertEqual(
            self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name),
            contract_initial_balance + required_approval,
        )

    def test_03_list_offer_negative_amounts(self):
        required_approval = Decimal("100.5")
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, required_approval)
        environment = {**self.environment, "now": TEST_DATETIME}

        # FIX: Update expected assertion message
        with self.assertRaisesRegex(AssertionError, "Offer amount must be positive"):
            self.otc_contract.list_offer(
                signer=self.maker_vk,
                environment=environment,
                offer_token=self.token_a_name,
                offer_amount=Decimal("-100"), # Pass Decimal
                take_token=self.token_b_name,
                take_amount=Decimal("50"),   # Pass Decimal
            )

        # FIX: Update expected assertion message
        with self.assertRaisesRegex(AssertionError, "Take amount must be positive"):
             self.otc_contract.list_offer(
                signer=self.maker_vk,
                environment=environment,
                offer_token=self.token_a_name,
                offer_amount=Decimal("100"), # Pass Decimal
                take_token=self.token_b_name,
                take_amount=Decimal("-50"),  # Pass Decimal
            )

    def test_04_list_offer_insufficient_allowance(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        required_approval = offer_amount + maker_fee
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, required_approval - Decimal("1"))
        environment = {**self.environment, "now": TEST_DATETIME}

        # Error comes from token contract, message should be stable
        with self.assertRaisesRegex(AssertionError, "Transfer amount exceeds allowance"):
            self.otc_contract.list_offer(
                signer=self.maker_vk,
                environment=environment,
                offer_token=self.token_a_name,
                offer_amount=offer_amount, # Pass Decimal
                take_token=self.token_b_name,
                take_amount=take_amount,   # Pass Decimal
            )

    def test_05_take_offer_happy_path(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        environment = {**self.environment, "now": TEST_DATETIME}
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk,
            environment=environment,
            offer_token=self.token_a_name,
            offer_amount=offer_amount, # Pass Decimal
            take_token=self.token_b_name,
            take_amount=take_amount,   # Pass Decimal
        )

        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)

        maker_token_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        maker_token_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.maker_vk)
        taker_token_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.taker_vk)
        taker_token_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.taker_vk)

        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        offer = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer["status"], "EXECUTED")
        self.assertEqual(offer["taker"], self.taker_vk)

        # FIX: Compare ContractingDecimal results with Decimal math directly
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.maker_vk), maker_token_b_bal + take_amount)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.maker_vk), maker_token_a_bal)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.taker_vk), taker_token_a_bal + offer_amount)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.taker_vk), taker_token_b_bal - taker_required_approval)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), maker_fee)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name), taker_fee)

    def test_06_take_offer_already_taken(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        # taker_fee is not strictly needed for this test flow but good for completeness if we were checking taker balances
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now, so environment is important
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount)

        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)
        # FIX: Removed environment argument as take_offer contract method doesn't use now
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        self._fund_account(self.token_b, self.other_vk, taker_required_approval) 
        self._approve_transfer(self.token_b, self.other_vk, self.otc_contract_name, taker_required_approval)
        
        with self.assertRaisesRegex(AssertionError, "Offer not available"):
            # FIX: Removed environment argument
            self.otc_contract.take_offer(signer=self.other_vk, listing_id=listing_id)

    def test_07_take_offer_non_existent(self):
        non_existent_id = "this_id_does_not_exist"
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, Decimal("50")) # Approve some amount

        with self.assertRaisesRegex(AssertionError, "Offer ID does not exist"): # CORRECTED Message
            self.otc_contract.take_offer(signer=self.taker_vk, listing_id=non_existent_id, environment=self.environment)

    def test_08_take_offer_insufficient_allowance(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount)

        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval - Decimal("1"))
        
        with self.assertRaisesRegex(AssertionError, "Transfer amount exceeds allowance"):
            # FIX: Removed environment argument as take_offer contract method doesn't use now
            self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

    def test_09_take_offer_maker_is_taker(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        current_fee_percent = self.otc_contract.fee.get()
        maker_fee = offer_amount / Decimal("100.0") * current_fee_percent
        taker_fee_for_maker = take_amount / Decimal("100.0") * current_fee_percent
        
        maker_required_approval_for_listing = offer_amount + maker_fee

        maker_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        self._fund_account(self.token_b, self.maker_vk, take_amount + taker_fee_for_maker)
        maker_initial_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.maker_vk)

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval_for_listing)
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount)
        
        maker_bal_a_after_list = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        self.assertEqual(maker_bal_a_after_list, maker_initial_a_bal - maker_required_approval_for_listing)

        maker_required_approval_for_taking = take_amount + taker_fee_for_maker
        self._approve_transfer(self.token_b, self.maker_vk, self.otc_contract_name, maker_required_approval_for_taking)

        # FIX: Removed environment argument as take_offer contract method doesn't use now
        self.otc_contract.take_offer(signer=self.maker_vk, listing_id=listing_id)

        offer = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer["status"], "EXECUTED")
        self.assertEqual(offer["taker"], self.maker_vk)

        expected_maker_final_a_bal = maker_initial_a_bal - maker_fee
        expected_maker_final_b_bal = maker_initial_b_bal - taker_fee_for_maker
        
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.maker_vk), expected_maker_final_a_bal)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.maker_vk), expected_maker_final_b_bal)
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), maker_fee)
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_b_name), taker_fee_for_maker)

    def test_10_cancel_offer_happy_path(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        required_approval = offer_amount + maker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, required_approval)
        maker_initial_balance = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        contract_initial_balance = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)

        environment = {**self.environment, "now": TEST_DATETIME}
        listing_id = self.otc_contract.list_offer(signer=self.maker_vk, environment=environment, offer_token=self.token_a_name, offer_amount=offer_amount, take_token=self.token_b_name, take_amount=take_amount)

        contract_balance_after_list = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        # FIX: Direct comparison
        self.assertEqual(contract_balance_after_list, contract_initial_balance + required_approval)

        self.otc_contract.cancel_offer(signer=self.maker_vk, listing_id=listing_id)

        offer = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer["status"], "CANCELLED")

        # FIX: Direct comparison
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.maker_vk), maker_initial_balance)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), contract_initial_balance)

    def test_11_cancel_offer_not_maker(self):
        offer_amount = Decimal("75.0"); take_amount = Decimal("25.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        required_approval = offer_amount + maker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, required_approval)
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount
        )
        offer_before_cancel_attempt = self.otc_contract.otc_listing[listing_id] 
        maker_balance_after_list = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        contract_balance_after_list = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)

        # Attempt to cancel by taker_vk (not the maker)
        with self.assertRaisesRegex(AssertionError, "Only maker can cancel offer"):
            # FIX: Removed environment argument as cancel_offer contract method doesn't use now
            self.otc_contract.cancel_offer(signer=self.taker_vk, listing_id=listing_id)

        # Verify offer status and balances are unchanged
        offer_after_cancel_attempt = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer_after_cancel_attempt["status"], "OPEN")
        self.assertEqual(offer_after_cancel_attempt, offer_before_cancel_attempt)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.maker_vk), maker_balance_after_list)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), contract_balance_after_list)

    def test_12_cancel_offer_non_existent(self):
        non_existent_id = "this_offer_does_not_exist_for_cancel"
        with self.assertRaisesRegex(AssertionError, "Offer ID does not exist"):
            self.otc_contract.cancel_offer(signer=self.maker_vk, listing_id=non_existent_id, environment=self.environment)

    def test_13_cancel_offer_already_executed(self):
        offer_amount = Decimal("60.0"); take_amount = Decimal("30.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        # List offer
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount
        )
        
        # Take offer
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)
        # FIX: Removed environment argument as take_offer contract method doesn't use now
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        offer_after_take = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer_after_take["status"], "EXECUTED")

        # Attempt to cancel by maker after it's executed
        with self.assertRaisesRegex(AssertionError, "Offer can not be cancelled"):
            # FIX: Removed environment argument as cancel_offer contract method doesn't use now
            self.otc_contract.cancel_offer(signer=self.maker_vk, listing_id=listing_id)

        # Verify offer status remains EXECUTED
        offer_after_cancel_attempt = self.otc_contract.otc_listing[listing_id]
        self.assertEqual(offer_after_cancel_attempt["status"], "EXECUTED")
        self.assertEqual(offer_after_cancel_attempt, offer_after_take)

    # Example for test_14
    def test_14_adjust_fee_happy_path(self):
        new_fee = Decimal("1.5")
        self.otc_contract.adjust_fee(signer=self.otc_owner_vk, trading_fee=new_fee) # Pass Decimal
        # FIX: Direct comparison
        self.assertEqual(self.otc_contract.fee.get(), new_fee)

        self.otc_contract.adjust_fee(signer=self.otc_owner_vk, trading_fee=Decimal("0.0"))
        # FIX: Direct comparison
        self.assertEqual(self.otc_contract.fee.get(), Decimal("0.0"))
        self.otc_contract.adjust_fee(signer=self.otc_owner_vk, trading_fee=Decimal("10.0"))
        # FIX: Direct comparison
        self.assertEqual(self.otc_contract.fee.get(), Decimal("10.0"))

    def test_15_adjust_fee_not_owner(self):
        original_fee = self.otc_contract.fee.get()
        new_fee = Decimal("2.0")
        
        with self.assertRaisesRegex(AssertionError, "Only owner can call this method!"): # CORRECTED message
            self.otc_contract.adjust_fee(signer=self.maker_vk, trading_fee=new_fee) # Environment not needed
        
        self.assertEqual(self.otc_contract.fee.get(), original_fee) 
        
        self.assertEqual(self.otc_contract.fee.get(), original_fee) 

    def test_16_adjust_fee_invalid_value(self):
        # FIX: Update expected assertion message
        with self.assertRaisesRegex(AssertionError, "Fee must be between 0.0 and 10.0 percent"):
            self.otc_contract.adjust_fee(signer=self.otc_owner_vk, trading_fee=Decimal("-0.1"))
        # FIX: Update expected assertion message
        with self.assertRaisesRegex(AssertionError, "Fee must be between 0.0 and 10.0 percent"):
            self.otc_contract.adjust_fee(signer=self.otc_owner_vk, trading_fee=Decimal("10.1"))
        # FIX: Direct comparison
        self.assertEqual(self.otc_contract.fee.get(), self.default_fee_percent)

    # Example for test_17
    def test_17_withdraw_happy_path(self):
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        environment = {**self.environment, "now": TEST_DATETIME}
        listing_id = self.otc_contract.list_offer(signer=self.maker_vk, environment=environment, offer_token=self.token_a_name, offer_amount=offer_amount, take_token=self.token_b_name, take_amount=take_amount)
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        # FIX: Direct comparison
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), maker_fee)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name), taker_fee)

        owner_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk)
        owner_initial_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.otc_owner_vk)

        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[self.token_a_name, self.token_b_name])

        # FIX: Direct comparison (compare with Decimal(0.0))
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), Decimal("0.0"))
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name), Decimal("0.0"))
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk), owner_initial_a_bal + maker_fee)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_b, self.otc_owner_vk), owner_initial_b_bal + taker_fee)

    def test_18_withdraw_not_owner(self):
        offer_amount = Decimal("10.0"); take_amount = Decimal("5.0")
        maker_fee = offer_amount / Decimal("100.0") * self.default_fee_percent
        taker_fee = take_amount / Decimal("100.0") * self.default_fee_percent
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, offer_amount + maker_fee)
        l_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=self.environment, # list_offer uses now
            offer_token=self.token_a_name, offer_amount=offer_amount, 
            take_token=self.token_b_name, take_amount=take_amount
        )
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, take_amount + taker_fee)
        # FIX: Removed environment argument as take_offer contract method doesn't use now
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=l_id)

        contract_earned_a_before = self.otc_contract.view_earned_fees(token=self.token_a_name)
        maker_bal_a_before = self._get_balance_contracting_or_zero(self.token_a, self.maker_vk)
        self.assertEqual(contract_earned_a_before, maker_fee)

        with self.assertRaisesRegex(AssertionError, "Only owner can call this method!"):
            self.otc_contract.withdraw(signer=self.maker_vk, token_list=[self.token_a_name])
        
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), contract_earned_a_before)
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.maker_vk), maker_bal_a_before)


    def test_19_withdraw_no_fees_to_withdraw(self):
        owner_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk)
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), Decimal("0.0"))
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), Decimal("0.0"))

        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[self.token_a_name], environment=self.environment)

        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk), owner_initial_a_bal)
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), Decimal("0.0"))
        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name), Decimal("0.0"))


    def test_20_withdraw_unknown_token_or_no_fees_for_specific_token(self):
        offer_amount_a = Decimal("100.0"); take_amount_b = Decimal("50.0")
        maker_fee_a = offer_amount_a / Decimal("100.0") * self.default_fee_percent
        taker_fee_b = take_amount_b / Decimal("100.0") * self.default_fee_percent

        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, offer_amount_a + maker_fee_a)
        
        # list_offer uses now from environment
        list_env = {"chain_id": "test-chain", "now": Datetime(year=2024, month=8, day=1, microsecond=1)}
        
        l_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=list_env, 
            offer_token=self.token_a_name, offer_amount=offer_amount_a, 
            take_token=self.token_b_name, take_amount=take_amount_b
        )
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, take_amount_b + taker_fee_b)
        
        # take_offer does not use now from environment in the contract
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=l_id)

        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), maker_fee_a)
        # Ensure self.token_c_name is defined in your class TestOtcContract
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_c_name), Decimal("0.0"))

        owner_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk)

        # Ensure self.token_c_name is defined in your class TestOtcContract
        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[self.token_a_name, self.token_c_name])

        self.assertEqual(self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk), owner_initial_a_bal + maker_fee_a)
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_a_name), Decimal("0.0"))
        # Ensure self.token_c_name is defined in your class TestOtcContract
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_c_name), Decimal("0.0"))
        self.assertEqual(self.otc_contract.view_earned_fees(token=self.token_b_name), taker_fee_b)


    def test_21_withdraw_cannot_take_escrowed_funds(self):
        # --- Phase 1: Generate some initial earned fees ---
        fee_offer_token = self.token_a_name
        fee_take_token = self.token_b_name
        fee_offer_amount = Decimal("10.0")
        fee_take_amount = Decimal("5.0")
        # FIX: Define fee_maker and fee_taker here
        fee_maker = self.maker_vk
        fee_taker = self.taker_vk

        fee_percent = self.default_fee_percent
        maker_fee_gen = fee_offer_amount / Decimal("100.0") * fee_percent
        taker_fee_gen = fee_take_amount / Decimal("100.0") * fee_percent

        # Fund and approve
        self._fund_account(self.token_a, fee_maker, fee_offer_amount + maker_fee_gen)
        self._fund_account(self.token_b, fee_taker, fee_take_amount + taker_fee_gen)
        self._approve_transfer(self.token_a, fee_maker, self.otc_contract_name, fee_offer_amount + maker_fee_gen)
        self._approve_transfer(self.token_b, fee_taker, self.otc_contract_name, fee_take_amount + taker_fee_gen)

        # List and take
        environment = {**self.environment, "now": Datetime(year=2025, month=1, day=1)}
        listing_id_gen = self.otc_contract.list_offer(
             signer=fee_maker, environment=environment,
             offer_token=fee_offer_token, offer_amount=fee_offer_amount,
             take_token=fee_take_token, take_amount=fee_take_amount
         )
        self.otc_contract.take_offer(signer=fee_taker, listing_id=listing_id_gen)

        # Verify earned fees (Direct comparison)
        self.assertEqual(self.otc_contract.view_earned_fees(token=fee_offer_token), maker_fee_gen)
        self.assertEqual(self.otc_contract.view_earned_fees(token=fee_take_token), taker_fee_gen)

        # Get balances (Direct comparison)
        owner_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk)
        owner_initial_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.otc_owner_vk)
        contract_initial_a_bal = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        contract_initial_b_bal = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(contract_initial_a_bal, maker_fee_gen)
        self.assertEqual(contract_initial_b_bal, taker_fee_gen)

        # --- Phase 2 ---
        main_offer_token = self.token_a_name
        main_offer_amount = Decimal("1000.0")
        main_take_token = self.token_b_name
        main_take_amount = Decimal("500.0")
        # FIX: Use a *different* maker for clarity, or just reuse self.maker_vk
        # Let's reuse self.maker_vk for simplicity as originally intended
        main_maker = self.maker_vk

        main_maker_fee = main_offer_amount / Decimal("100.0") * fee_percent
        main_total_escrow = main_offer_amount + main_maker_fee

        # Fund and approve
        # We need to ensure the main_maker has enough *additional* funds
        # _fund_account adds to existing balance, so this is fine.
        self._fund_account(self.token_a, main_maker, main_total_escrow)
        self._approve_transfer(self.token_a, main_maker, self.otc_contract_name, main_total_escrow)

        main_maker_balance_before_list = self._get_balance_contracting_or_zero(self.token_a, main_maker)

        # List main offer
        environment2 = {**self.environment, "now": Datetime(year=2025, month=1, day=2)}
        self.otc_contract.list_offer(
            signer=main_maker, environment=environment2,
            offer_token=main_offer_token, offer_amount=main_offer_amount,
            take_token=main_take_token, take_amount=main_take_amount
        )

        # --- Phase 2 Verification ---
        expected_main_maker_balance_after_list = main_maker_balance_before_list - main_total_escrow
        actual_main_maker_balance_after_list = self._get_balance_contracting_or_zero(self.token_a, main_maker)
        self.assertEqual(actual_main_maker_balance_after_list, expected_main_maker_balance_after_list)

        expected_contract_a_bal_after_list = contract_initial_a_bal + main_total_escrow
        self.assertEqual(self.otc_contract.view_earned_fees(token=main_offer_token), maker_fee_gen)

        # --- Phase 3: Withdraw ---
        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[main_offer_token, main_take_token])

        # --- Phase 4: Verification ---
        # NOTE: The funding logic in phase 2 comes from the owner by default in _fund_account
        # We need to account for this owner expenditure when calculating expected final owner balance
        expected_owner_a_bal_final = owner_initial_a_bal - main_total_escrow + maker_fee_gen # Owner funded main_maker
        expected_owner_b_bal_final = owner_initial_b_bal + taker_fee_gen # Owner did not fund for token B escrow

        actual_owner_a_bal_after_withdraw = self._get_balance_contracting_or_zero(self.token_a, self.otc_owner_vk)
        self.assertEqual(actual_owner_a_bal_after_withdraw, expected_owner_a_bal_final)

        actual_owner_b_bal_after_withdraw = self._get_balance_contracting_or_zero(self.token_b, self.otc_owner_vk)
        self.assertEqual(actual_owner_b_bal_after_withdraw, expected_owner_b_bal_final)

        self.assertEqual(self.otc_contract.view_earned_fees(token=main_offer_token), Decimal("0.0"))
        self.assertEqual(self.otc_contract.view_earned_fees(token=main_take_token), Decimal("0.0"))

        expected_contract_a_bal_after_withdraw = expected_contract_a_bal_after_list - maker_fee_gen
        actual_contract_a_bal_after_withdraw = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        self.assertEqual(actual_contract_a_bal_after_withdraw, main_total_escrow, "Contract A balance after withdraw != escrow amount")
        self.assertEqual(actual_contract_a_bal_after_withdraw, expected_contract_a_bal_after_withdraw, "Contract A balance after withdraw doesn't match calculation")

        actual_contract_b_bal_after_withdraw = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(actual_contract_b_bal_after_withdraw, Decimal("0.0"))


    # Make sure all other tests also use direct comparisons where needed

    def test_22_view_earned_fees_accuracy(self):
        """Verify the view_earned_fees method reports correct amounts using existing tokens."""
        # --- Verification 0: Check Earned Fees Before Any Trade in this Test ---
        # Since setUp runs for each test, earned fees should start at 0
        initial_earned_a = self.otc_contract.view_earned_fees(token=self.token_a_name)
        initial_earned_b = self.otc_contract.view_earned_fees(token=self.token_b_name)
        self.assertEqual(initial_earned_a, Decimal("0.0"), "Initial earned fee for Token A should be 0.0")
        self.assertEqual(initial_earned_b, Decimal("0.0"), "Initial earned fee for Token B should be 0.0")

        # --- Setup: Generate Fees ---
        offer_amount = Decimal("200.0")
        take_amount = Decimal("100.0")
        fee_percent = self.default_fee_percent # Use the default for simplicity
        maker_fee = offer_amount / Decimal("100.0") * fee_percent
        taker_fee = take_amount / Decimal("100.0") * fee_percent
        maker_required_approval = offer_amount + maker_fee
        taker_required_approval = take_amount + taker_fee

        # Approve and list
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        environment_list = {**self.environment, "now": Datetime(year=2026, month=1, day=1)}
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=environment_list,
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount
        )

        # Approve and take
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        # --- Verification 1: Check Earned Fees After Trade ---
        earned_a = self.otc_contract.view_earned_fees(token=self.token_a_name)
        earned_b = self.otc_contract.view_earned_fees(token=self.token_b_name)

        self.assertEqual(earned_a, maker_fee, "Earned fee for Token A is incorrect after trade")
        self.assertEqual(earned_b, taker_fee, "Earned fee for Token B is incorrect after trade")

        # --- Verification 2: Check Earned Fees After Withdrawal ---
        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[self.token_a_name, self.token_b_name])

        earned_a_after_withdraw = self.otc_contract.view_earned_fees(token=self.token_a_name)
        earned_b_after_withdraw = self.otc_contract.view_earned_fees(token=self.token_b_name)

        self.assertEqual(earned_a_after_withdraw, Decimal("0.0"), "Earned fee for Token A should be 0.0 after withdrawal")
        self.assertEqual(earned_b_after_withdraw, Decimal("0.0"), "Earned fee for Token B should be 0.0 after withdrawal")


    def test_23_view_contract_balance_accuracy(self):
        """Verify view_contract_balance matches actual contract token balance using existing tokens."""
        # --- Verification 0: Initial Balances ---
        # Check balances right after setUp, should be 0
        initial_view_bal_a = self.otc_contract.view_contract_balance(token=self.token_a_name)
        initial_actual_bal_a = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        self.assertEqual(initial_actual_bal_a, Decimal("0.0"), "Initial actual Token A balance should be 0")
        self.assertEqual(initial_view_bal_a, initial_actual_bal_a, "Initial view balance A != Initial actual balance")

        initial_view_bal_b = self.otc_contract.view_contract_balance(token=self.token_b_name)
        initial_actual_bal_b = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(initial_actual_bal_b, Decimal("0.0"), "Initial actual Token B balance should be 0")
        self.assertEqual(initial_view_bal_b, initial_actual_bal_b, "Initial view balance B != Initial actual balance")

        # --- Setup Phase 1: List an Offer (Escrow Token A) ---
        offer_amount = Decimal("300.0")
        take_amount = Decimal("150.0")
        fee_percent = self.default_fee_percent
        maker_fee = offer_amount / Decimal("100.0") * fee_percent
        taker_fee = take_amount / Decimal("100.0") * fee_percent # Needed later
        total_escrow_a = offer_amount + maker_fee
        maker_required_approval = total_escrow_a

        # List the offer
        self._approve_transfer(self.token_a, self.maker_vk, self.otc_contract_name, maker_required_approval)
        environment_list = {**self.environment, "now": Datetime(year=2026, month=2, day=1)}
        listing_id = self.otc_contract.list_offer(
            signer=self.maker_vk, environment=environment_list,
            offer_token=self.token_a_name, offer_amount=offer_amount,
            take_token=self.token_b_name, take_amount=take_amount
        )

        # --- Verification 1: Balance After Listing ---
        # Check Token A (escrowed)
        view_bal_a_after_list = self.otc_contract.view_contract_balance(token=self.token_a_name)
        actual_bal_a_after_list = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        self.assertEqual(actual_bal_a_after_list, total_escrow_a, "Actual Token A balance mismatch after listing")
        self.assertEqual(view_bal_a_after_list, actual_bal_a_after_list, "View balance A != Actual balance after listing")

        # Check Token B (should still be 0)
        view_bal_b_after_list = self.otc_contract.view_contract_balance(token=self.token_b_name)
        actual_bal_b_after_list = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(actual_bal_b_after_list, Decimal("0.0"), "Actual Token B balance should be 0 after listing A")
        self.assertEqual(view_bal_b_after_list, actual_bal_b_after_list, "View balance B != Actual balance after listing A")

        # --- Setup Phase 2: Take the Offer ---
        taker_required_approval = take_amount + taker_fee
        self._approve_transfer(self.token_b, self.taker_vk, self.otc_contract_name, taker_required_approval)
        self.otc_contract.take_offer(signer=self.taker_vk, listing_id=listing_id)

        # --- Verification 2: Balance After Taking (Fee Amounts) ---
        # Check Token A (maker_fee)
        view_bal_a_after_take = self.otc_contract.view_contract_balance(token=self.token_a_name)
        actual_bal_a_after_take = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        self.assertEqual(actual_bal_a_after_take, maker_fee, "Actual Token A balance mismatch after take (should be maker_fee)")
        self.assertEqual(view_bal_a_after_take, actual_bal_a_after_take, "View balance A != Actual balance after take")

        # Check Token B (taker_fee)
        view_bal_b_after_take = self.otc_contract.view_contract_balance(token=self.token_b_name)
        actual_bal_b_after_take = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(actual_bal_b_after_take, taker_fee, "Actual Token B balance mismatch after take (should be taker_fee)")
        self.assertEqual(view_bal_b_after_take, actual_bal_b_after_take, "View balance B != Actual balance after take")

        # --- Setup Phase 3: Withdraw Fees ---
        self.otc_contract.withdraw(signer=self.otc_owner_vk, token_list=[self.token_a_name, self.token_b_name])

        # --- Verification 3: Balance After Withdrawal (Zero) ---
        # Check Token A (0)
        view_bal_a_after_withdraw = self.otc_contract.view_contract_balance(token=self.token_a_name)
        actual_bal_a_after_withdraw = self._get_balance_contracting_or_zero(self.token_a, self.otc_contract_name)
        self.assertEqual(actual_bal_a_after_withdraw, Decimal("0.0"), "Actual Token A balance mismatch after withdraw")
        self.assertEqual(view_bal_a_after_withdraw, actual_bal_a_after_withdraw, "View balance A != Actual balance after withdraw")

        # Check Token B (0)
        view_bal_b_after_withdraw = self.otc_contract.view_contract_balance(token=self.token_b_name)
        actual_bal_b_after_withdraw = self._get_balance_contracting_or_zero(self.token_b, self.otc_contract_name)
        self.assertEqual(actual_bal_b_after_withdraw, Decimal("0.0"), "Actual Token B balance mismatch after withdraw")
        self.assertEqual(view_bal_b_after_withdraw, actual_bal_b_after_withdraw, "View balance B != Actual balance after withdraw")

    def test_24_reentrancy_exploit_vulnerable_otc(self):
        # --- Setup for the exploit ---
        # 1. Deploy the vulnerable OTC contract
        vulnerable_otc = self._deploy_contract_from_file(
            "con_otc_vulnerable.py", 
            self.vulnerable_otc_name_for_exploit, 
            self.otc_owner_vk 
        )
        
        # 2. Deploy the malicious contract (con_breakotc)
        exploit_contract = self._deploy_contract_from_file(
            "con_breakotc.py", 
            self.exploit_contract_name, 
            self.attacker_vk 
        )

        # 3. Define tokens
        token_a_contract = self.token_a # Attacker offers this, it will be the target of theft by exploit_contract
        token_a_name = self.token_a_name
        
        otc_fee_percent = vulnerable_otc.fee.get()

        # --- Phase 1: Fund Vulnerable OTC with Token A (Simulates general liquidity) ---
        otc_initial_token_a_liquidity = Decimal("500.0")
        self._fund_account(token_a_contract, self.vulnerable_otc_name_for_exploit, otc_initial_token_a_liquidity)
        initial_otc_token_a_bal = self._get_balance_contracting_or_zero(token_a_contract, self.vulnerable_otc_name_for_exploit)
        self.assertEqual(initial_otc_token_a_bal, otc_initial_token_a_liquidity)

        # --- Phase 2: Attacker lists Offer_X ---
        # Attacker offers Token A and wants to take their own ExploitToken.
        offer_X_offer_TokenA_amount = Decimal("100.0")
        offer_X_take_ExploitToken_amount = Decimal("10.0")

        # Attacker needs Token A to make the offer
        self._fund_account(token_a_contract, self.attacker_vk, offer_X_offer_TokenA_amount * Decimal("2.0")) # Ensure enough for offer + fee -> 200 TokenA

        offer_X_maker_TokenA_fee = offer_X_offer_TokenA_amount * otc_fee_percent / Decimal("100.0")
        
        # Attacker approves vulnerable_otc to spend their Token A
        self._approve_transfer(token_a_contract, self.attacker_vk, self.vulnerable_otc_name_for_exploit, offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee)
        
        list_env_offer_X = {"chain_id": "test-chain", "now": TEST_DATETIME_LIST_EXPLOIT}
        listing_id_Offer_X = vulnerable_otc.list_offer(
            signer=self.attacker_vk, 
            environment=list_env_offer_X,
            offer_token=token_a_name,                      # Attacker offers Token A
            offer_amount=offer_X_offer_TokenA_amount,
            take_token=self.exploit_contract_name,        # Attacker wants ExploitToken
            take_amount=offer_X_take_ExploitToken_amount  
        )
        self.assertIsNotNone(listing_id_Offer_X, "Listing ID for Attacker's Offer_X is None.")
        # Now, (initial_otc_token_a_bal + offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee) of Token A is in vulnerable_otc.
        otc_holds_token_a = initial_otc_token_a_bal + offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee
        self.assertEqual(self._get_balance_contracting_or_zero(token_a_contract, self.vulnerable_otc_name_for_exploit), otc_holds_token_a)

        # --- Phase 3: Attacker prepares con_breakotc for exploit ---
        # The re-entrant call will target Offer_X itself.
        exploit_contract.setlisting(l=listing_id_Offer_X, signer=self.attacker_vk)
        exploit_contract.setrec(l=5, signer=self.attacker_vk) # Enable five re-entrant calls. More than five calls leads to "AssertionError: Transfer amount exceeds balance!"
        # con_breakotc will steal the offer_token of listing_id_Offer_X, which is token_a_name
        exploit_contract.setstole(l=token_a_name, signer=self.attacker_vk) 

        # --- Phase 4: Attacker takes THEIR OWN Offer_X ---
        # Attacker (as TAKER of Offer_X) needs to "pay" with ExploitToken.
        offer_X_taker_ExploitToken_fee = offer_X_take_ExploitToken_amount * otc_fee_percent / Decimal("100.0")
        
        self._approve_transfer(exploit_contract, self.attacker_vk, self.vulnerable_otc_name_for_exploit, offer_X_take_ExploitToken_amount + offer_X_taker_ExploitToken_fee)

        # Record balances before the critical transaction by attacker
        attacker_token_a_bal_before_take_X = self._get_balance_contracting_or_zero(token_a_contract, self.attacker_vk)
        # Attacker's balance of their own ExploitToken (maker of Offer_X)
        attacker_exploit_token_bal_before_take_X = self._get_balance_contracting_or_zero(exploit_contract, self.attacker_vk)
         
        
        # Attacker (signer) takes their own Offer_X.
        # vulnerable_otc will attempt to pay `offer_X_take_ExploitToken_amount` of `exploit_contract_name` to `attacker_vk` (as the maker of Offer_X).
        # This payment call to `exploit_contract.transfer(...)` is the re-entrancy trigger.
        vulnerable_otc.take_offer(listing_id=listing_id_Offer_X, signer=self.attacker_vk)

        # Record balances after the critical transaction by attacker
        attacker_token_a_bal_after_take_X = self._get_balance_contracting_or_zero(token_a_contract, self.attacker_vk)

        # --- Verify post-exploit state ---
        
        # 1. Attacker's Offer_X status and taker (modified by the inner re-entrant call)
        offer_X_state_after_exploit = vulnerable_otc.otc_listing[listing_id_Offer_X]
        self.assertEqual(offer_X_state_after_exploit["status"], "EXECUTED", "Attacker's Offer_X status should be EXECUTED by inner call")        

        # 2. Attacker (self.attacker_vk) gets Token A (stolen via exploit_contract during inner take of Offer_X)
        # Inner take_offer(Offer_X) by exploit_contract:
        #   - `offer_token` is `token_a_name`, `offer_amount` is `offer_X_offer_TokenA_amount`.
        #   - `vulnerable_otc` pays `offer_X_offer_TokenA_amount` of Token A to `exploit_contract` (as taker of inner call).
        #   - `exploit_contract.transfer` then sweeps this Token A to `attacker_vk`.
        amount_of_token_a_stolen = attacker_token_a_bal_after_take_X - attacker_token_a_bal_before_take_X
        self.assertGreater(amount_of_token_a_stolen, otc_initial_token_a_liquidity, "Attacker did not drain liquidity")

        # 3. Vulnerable OTC's Token A balance
        # Initial in OTC from attacker's listing: `otc_holds_token_a`
        # Inner take_offer(Offer_X):
        #   - `exploit_contract` (as taker) pays fee for Offer_X using `exploit_contract_token`.
        #   - `vulnerable_otc` pays `offer_X_offer_TokenA_amount` of Token A to `exploit_contract`.
        # Net change for OTC's Token A: -offer_X_offer_TokenA_amount (paid to exploit_contract).
        # The fee collected by OTC *for Token A* in Offer_X was `offer_X_maker_TokenA_fee`, already part of `otc_holds_token_a`.
        # amount of token_a left in the vulnerable OTC contract is 0.5
        otc_token_a_liquidity_left =  otc_holds_token_a - amount_of_token_a_stolen
        # OTC should be left with only offer_X_maker_TokenA_fee -> 0.5 TokenA
        self.assertEqual(self._get_balance_contracting_or_zero(token_a_contract, self.vulnerable_otc_name_for_exploit), otc_token_a_liquidity_left, "OTC Token A should only have attacker's maker fee left.")
        
        # 4. Attacker's balance of ExploitToken:
        #    Attacker is the maker of Offer_X, expecting `offer_X_take_ExploitToken_amount`.
        #    Attacker is also the taker of Offer_X (outer call, though it fails).
        #    The inner `take_offer` by `exploit_contract`:
        #       - `vulnerable_otc` pays `offer_X_take_ExploitToken_amount` to `attacker_vk` (as maker of Offer_X).

        # Attacker minted more of their Exploit tokens to themselves in the process
        total_supply_of_exploit_tokens = attacker_exploit_token_bal_before_take_X
        self.assertGreater(self._get_balance_contracting_or_zero(exploit_contract, self.attacker_vk), total_supply_of_exploit_tokens)
        
        # 5. Earned fees in vulnerable OTC from the *inner successful trade* (Attacker's Offer_X taken by exploit_contract):
        #    Fee on offer_token (Token A, paid by attacker when listing): offer_X_maker_TokenA_fee
        #    Fee on take_token (ExploitToken, paid by exploit_contract as taker in inner call): offer_X_taker_ExploitToken_fee
        # why are they inflated?
        self.assertGreater(vulnerable_otc.view_earned_fees(token=token_a_name), offer_X_maker_TokenA_fee) # 3 > 0.5
        self.assertGreater(vulnerable_otc.view_earned_fees(token=self.exploit_contract_name), offer_X_taker_ExploitToken_fee) # 0.3 > 0.05
    
    def test_25_reentrancy_exploit_safeguarded_otc(self):
        # --- Setup for the exploit ---
        # 1. Deploy the vulnerable OTC contract
        safeguarded_otc = self._deploy_contract_from_file(
            "con_otc_v3.py", 
            self.safeguarded_otc_name_for_exploit, 
            self.otc_owner_vk 
        )
        
        # 2. Deploy the malicious contract (con_breakotc)
        exploit_contract = self._deploy_contract_from_file(
            "con_breakotcV3.py", 
            self.exploit_contract_name, 
            self.attacker_vk 
        )

        # 3. Define tokens
        token_a_contract = self.token_a # Attacker offers this, it will be the target of theft by exploit_contract
        token_a_name = self.token_a_name
        
        otc_fee_percent = safeguarded_otc.fee.get()

        # --- Phase 1: Fund Vulnerable OTC with Token A (Simulates general liquidity) ---
        otc_initial_token_a_liquidity = Decimal("500.0")
        self._fund_account(token_a_contract, self.safeguarded_otc_name_for_exploit, otc_initial_token_a_liquidity)
        initial_otc_token_a_bal = self._get_balance_contracting_or_zero(token_a_contract, self.safeguarded_otc_name_for_exploit)
        self.assertEqual(initial_otc_token_a_bal, otc_initial_token_a_liquidity)

        # --- Phase 2: Attacker lists Offer_X ---
        # Attacker offers Token A and wants to take their own ExploitToken.
        offer_X_offer_TokenA_amount = Decimal("100.0")
        offer_X_take_ExploitToken_amount = Decimal("10.0")

        # Attacker needs Token A to make the offer
        self._fund_account(token_a_contract, self.attacker_vk, offer_X_offer_TokenA_amount * Decimal("2.0")) # Ensure enough for offer + fee -> 200 TokenA

        offer_X_maker_TokenA_fee = offer_X_offer_TokenA_amount * otc_fee_percent / Decimal("100.0")
        
        # Attacker approves safeguarded_otc to spend their Token A
        self._approve_transfer(token_a_contract, self.attacker_vk, self.safeguarded_otc_name_for_exploit, offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee)
        
        list_env_offer_X = {"chain_id": "test-chain", "now": TEST_DATETIME_LIST_EXPLOIT}
        listing_id_Offer_X = safeguarded_otc.list_offer(
            signer=self.attacker_vk, 
            environment=list_env_offer_X,
            offer_token=token_a_name,                      # Attacker offers Token A
            offer_amount=offer_X_offer_TokenA_amount,
            take_token=self.exploit_contract_name,        # Attacker wants ExploitToken
            take_amount=offer_X_take_ExploitToken_amount  
        )
        self.assertIsNotNone(listing_id_Offer_X, "Listing ID for Attacker's Offer_X is None.")
        # Now, (initial_otc_token_a_bal + offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee) of Token A is in safeguarded_otc.
        otc_holds_token_a = initial_otc_token_a_bal + offer_X_offer_TokenA_amount + offer_X_maker_TokenA_fee
        self.assertEqual(self._get_balance_contracting_or_zero(token_a_contract, self.safeguarded_otc_name_for_exploit), otc_holds_token_a)

        # --- Phase 3: Attacker prepares con_breakotc for exploit ---
        # The re-entrant call will target Offer_X itself.
        exploit_contract.setlisting(l=listing_id_Offer_X, signer=self.attacker_vk)
        exploit_contract.setrec(l=5, signer=self.attacker_vk) # Enable five re-entrant calls. More than five calls leads to "AssertionError: Transfer amount exceeds balance!"
        # con_breakotc will steal the offer_token of listing_id_Offer_X, which is token_a_name
        exploit_contract.setstole(l=token_a_name, signer=self.attacker_vk) 

        # --- Phase 4: Attacker takes THEIR OWN Offer_X ---
        # Attacker (as TAKER of Offer_X) needs to "pay" with ExploitToken.
        offer_X_taker_ExploitToken_fee = offer_X_take_ExploitToken_amount * otc_fee_percent / Decimal("100.0")
        
        self._approve_transfer(exploit_contract, self.attacker_vk, self.safeguarded_otc_name_for_exploit, offer_X_take_ExploitToken_amount + offer_X_taker_ExploitToken_fee)

        # Record balances before the critical transaction by attacker
        attacker_token_a_bal_before_take_X = self._get_balance_contracting_or_zero(token_a_contract, self.attacker_vk)
        # Attacker's balance of their own ExploitToken (maker of Offer_X)         
        
        # Attacker (signer) takes their own Offer_X.
        # safeguarded_otc will attempt to pay `offer_X_take_ExploitToken_amount` of `exploit_contract_name` to `attacker_vk` (as the maker of Offer_X).
        # This payment call to `exploit_contract.transfer(...)` is the re-entrancy trigger.
        with self.assertRaisesRegex(AssertionError, "Contract is busy, please try again."):
            safeguarded_otc.take_offer(listing_id=listing_id_Offer_X, signer=self.attacker_vk)

        # Record balances after the critical transaction by attacker
        attacker_token_a_bal_after_take_X = self._get_balance_contracting_or_zero(token_a_contract, self.attacker_vk)

        # --- Verify post-exploit state ---
        
        # 1. Attacker's Offer_X status and taker (modified by the inner re-entrant call)
        
        offer_X_state_after_exploit = safeguarded_otc.otc_listing[listing_id_Offer_X]
        with self.assertRaisesRegex(AssertionError, "Attacker's attempt was not EXECUTED by inner call"):
            self.assertEqual(offer_X_state_after_exploit["status"], "EXECUTED", "Attacker's attempt was not EXECUTED by inner call")        

        # 2. Attacker (self.attacker_vk) gets Token A (stolen via exploit_contract during inner take of Offer_X)
        # Inner take_offer(Offer_X) by exploit_contract:
        #   - `offer_token` is `token_a_name`, `offer_amount` is `offer_X_offer_TokenA_amount`.
        #   - `safeguarded_otc` pays `offer_X_offer_TokenA_amount` of Token A to `exploit_contract` (as taker of inner call).
        #   - `exploit_contract.transfer` then sweeps this Token A to `attacker_vk`.
        amount_of_token_a_stolen = attacker_token_a_bal_after_take_X - attacker_token_a_bal_before_take_X
        with self.assertRaisesRegex(AssertionError, "Attacker did not drain liquidity"):
            self.assertGreater(amount_of_token_a_stolen, otc_initial_token_a_liquidity, "Attacker did not drain liquidity")

    # (Assuming con_otc_v3.py is the name of your safeguarded contract file)
    # Add this definition to your TestOtcContract class variables
    # self.safeguarded_otc_name_for_exploit = "con_otc_safeguarded" # Or similar unique name

    def test_26_guard_failure_recovery_via_atomicity(self):
        # 1. Deploy the safeguarded OTC contract
        safeguarded_otc = self._deploy_contract_from_file(
            "con_otc_v3.py",  # Use the filename of your patched contract
            "con_otc_safeguarded_for_recovery_test", # Unique name for this test instance
            self.otc_owner_vk
        )

        # 2. Verify initial guard state (should be False)
        self.assertEqual(safeguarded_otc.reentrancyGuardActive.get(), False, "Guard should be initially false.")

        # 3. Prepare for a call to list_offer that will fail an assertion
        #    AFTER the guard is set but BEFORE it's released.
        #    We'll use offer_amount = 0, which fails: assert offer_amount > decimal("0.0")
        offer_token_name = self.token_a_name
        zero_offer_amount = Decimal("0.0") # This will cause the assertion to fail
        take_token_name = self.token_b_name
        valid_take_amount = Decimal("10.0")

        # Attacker (or any user) needs to approve tokens for the list_offer attempt,
        # even if it's expected to fail. The transfer_from is later.
        # For this specific assertion (amount > 0), no prior transfer_from is strictly needed
        # for the assertion itself to be hit.

        environment_for_failure = {"chain_id": "test-chain", "now": TEST_DATETIME}

        # 4. Attempt the list_offer call that should fail internally
        with self.assertRaisesRegex(AssertionError, "Offer amount must be positive"):
            safeguarded_otc.list_offer(
                signer=self.maker_vk,
                environment=environment_for_failure,
                offer_token=offer_token_name,
                offer_amount=zero_offer_amount, # This will fail the internal check
                take_token=take_token_name,
                take_amount=valid_take_amount,
            )

        # 5. Verify guard state AFTER the failed transaction
        # Due to transaction atomicity, the reentrancyGuardActive should have been rolled back to False.
        self.assertEqual(safeguarded_otc.reentrancyGuardActive.get(), False,
                         "Guard should be false after a failed transaction due to atomicity.")

        # 6. Verify contract usability by making a successful call
        # This proves the contract is not locked.
        valid_offer_amount = Decimal("100.0")
        required_approval_for_valid_offer = valid_offer_amount + (valid_offer_amount * safeguarded_otc.fee.get() / Decimal("100.0"))
        self._approve_transfer(self.token_a, self.maker_vk, "con_otc_safeguarded_for_recovery_test", required_approval_for_valid_offer)

        environment_for_success = {"chain_id": "test-chain", "now": TEST_DATETIME_PLUS_1SEC}
        try:
            listing_id_successful = safeguarded_otc.list_offer(
                signer=self.maker_vk,
                environment=environment_for_success,
                offer_token=offer_token_name,
                offer_amount=valid_offer_amount,
                take_token=take_token_name,
                take_amount=valid_take_amount,
            )
            self.assertIsNotNone(listing_id_successful, "Successful listing should return an ID.")
        except Exception as e:
            self.fail(f"Subsequent successful call failed, contract might be locked or another issue: {e}")

        # 7. Verify guard state again after a successful transaction (should also be False)
        self.assertEqual(safeguarded_otc.reentrancyGuardActive.get(), False,
                         "Guard should be false after a successful transaction.")

    # Miscellaneous ------------------------------------------------------------------------------------------

    def test_27_event_emission_list_offer(self):
        # 1. Deploy the safeguarded OTC contract
        safeguarded_otc_contract_name = "con_otc_event_test"
        safeguarded_otc = self._deploy_contract_from_file(
            "con_otc_v3.py",  # Assuming this is your patched contract
            safeguarded_otc_contract_name,
            self.otc_owner_vk
        )

        # 2. Setup for list_offer
        offer_amount = Decimal("100.0")
        take_amount = Decimal("50.0")
        current_fee_percent = safeguarded_otc.fee.get()
        maker_fee = offer_amount / Decimal("100.0") * current_fee_percent
        required_approval = offer_amount + maker_fee

        self._approve_transfer(self.token_a, self.maker_vk, safeguarded_otc_contract_name, required_approval)

        environment_list = {"chain_id": "test-chain", "now": TEST_DATETIME}

        # 3. Call list_offer and request full output to get events
        tx_output = safeguarded_otc.list_offer(
            signer=self.maker_vk,
            environment=environment_list,
            offer_token=self.token_a_name,
            offer_amount=offer_amount,
            take_token=self.token_b_name,
            take_amount=take_amount,
            return_full_output=True  # <-- KEY CHANGE TO GET EVENTS
        )

        # 4. Verify the transaction was successful and events are present
        self.assertEqual(tx_output['status_code'], 0, f"List offer failed: {tx_output.get('result')}")
        self.assertIn('events', tx_output)
        self.assertIsInstance(tx_output['events'], list)
        self.assertEqual(len(tx_output['events']), 1, "Expected one event to be emitted.")

        # 5. Inspect the emitted event
        emitted_event = tx_output['events'][0]
        listing_id_from_result = tx_output['result'] # The list_offer function returns the listing_id

        # Expected event structure (based on LogEvent.write_event)
        # event = {
        #     "contract": contract, # Name of the contract that DEFINED the event (e.g., con_otc_event_test)
        #     "event": self._event, # The event name (e.g., "Offer")
        #     "signer": self._signer, # Signer of the transaction
        #     "caller": caller, # Caller of list_offer (self.maker_vk)
        #     "data_indexed": { ... },
        #     "data": { ... },
        # }

        self.assertEqual(emitted_event['contract'], safeguarded_otc_contract_name)
        self.assertEqual(emitted_event['event'], "Offer")
        self.assertEqual(emitted_event['signer'], self.maker_vk) # Signer of this specific tx
        self.assertEqual(emitted_event['caller'], self.maker_vk) # Caller of list_offer

        # Verify indexed data
        self.assertIn('id', emitted_event['data_indexed'])
        self.assertEqual(emitted_event['data_indexed']['id'], listing_id_from_result)
        self.assertIn('taker', emitted_event['data_indexed'])
        self.assertEqual(emitted_event['data_indexed']['taker'], "None") # As per OfferEvent params
        self.assertIn('status', emitted_event['data_indexed'])
        self.assertEqual(emitted_event['data_indexed']['status'], "OPEN")

        # Verify non-indexed data
        self.assertIn('maker', emitted_event['data'])
        self.assertEqual(emitted_event['data']['maker'], self.maker_vk)
        self.assertIn('offer_token', emitted_event['data'])
        self.assertEqual(emitted_event['data']['offer_token'], self.token_a_name)
        self.assertIn('offer_amount', emitted_event['data'])
        self.assertEqual(emitted_event['data']['offer_amount'], offer_amount)
        self.assertIn('take_token', emitted_event['data'])
        self.assertEqual(emitted_event['data']['take_token'], self.token_b_name)
        self.assertIn('take_amount', emitted_event['data'])
        self.assertEqual(emitted_event['data']['take_amount'], take_amount)
        self.assertIn('date_listed', emitted_event['data'])
        self.assertEqual(emitted_event['data']['date_listed'], str(TEST_DATETIME))
        self.assertIn('fee', emitted_event['data'])
        self.assertEqual(emitted_event['data']['fee'], current_fee_percent)

        # 6. Sanity check: verify the returned result is still the listing ID
        self.assertIsInstance(listing_id_from_result, str)

if __name__ == "__main__":
    unittest.main()