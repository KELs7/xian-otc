random.seed()
I = importlib  # noqa: E741

# State Variables
fee = Variable()
otc_listing = Hash()
owner = Variable()
earned_fees = Hash(default_value=decimal("0.0")) # track withdrawable fees per token


@construct
def init():
    owner.set(ctx.caller)
    # Initialize fee as decimal
    fee.set(decimal("0.5"))

@export
def list_offer(
    offer_token: str,
    offer_amount: float,  # Use decimal
    take_token: str,
    take_amount: float   # Use decimal
):
    assert offer_amount > decimal("0.0"), "Offer amount must be positive"
    assert take_amount > decimal("0.0"), "Take amount must be positive"
    # listing_id = f"{ctx.caller[:7]}-{offer_token}-{take_token}-{now}"
    listing_id = hashlib.sha256(str(now) + str(random.randrange(99)))
    assert not otc_listing[listing_id], "Generated ID not unique. Try again"
    maker_fee = offer_amount / 100 * fee.get()
    I.import_module(offer_token).transfer_from(
        amount=offer_amount + maker_fee,
        to=ctx.this,
        main_account=ctx.caller
    )

    otc_listing[listing_id] = {
        "maker": ctx.caller,
        "taker": None,
        "offer_token": offer_token,
        "offer_amount": offer_amount,
        "take_token": take_token,
        "take_amount": take_amount,
        "fee": fee.get(),
        "status": "OPEN",
    }
    return listing_id


@export
def take_offer(listing_id: str):
    offer = otc_listing[listing_id]
    assert offer, "Offer ID does not exist" # Check existence first
    assert offer["status"] == "OPEN", "Offer not available"

    # Use stored decimal amounts and fee for calculation
    offer_fee_percent = offer["fee"] # Use the fee % from when the offer was made
    taker_fee = offer["take_amount"] / decimal("100.0") * offer_fee_percent
    maker_fee = offer["offer_amount"] / decimal("100.0") * offer_fee_percent # Recalculate for fee accumulation clarity

    # --- Secure Taker Funds ---
    # Transfer take_token amount + taker_fee to this contract from taker (using decimal)
    I.import_module(offer["take_token"]).transfer_from(
        amount=offer["take_amount"] + taker_fee,
        to=ctx.this,
        main_account=ctx.caller
    )

    # --- Fee Accumulation Point ---
    # Fees are now "earned" as the trade is irreversible from here (assuming atomicity)
    # Use decimal directly
    current_maker_fee_earned = earned_fees[offer["offer_token"]] # Default is decimal("0.0")
    earned_fees[offer["offer_token"]] = current_maker_fee_earned + maker_fee

    current_taker_fee_earned = earned_fees[offer["take_token"]] # Default is decimal("0.0")
    earned_fees[offer["take_token"]] = current_taker_fee_earned + taker_fee

    # --- Settlement Transfers ---
    # transfer take_token amount to maker
    I.import_module(offer["take_token"]).transfer(
        amount=offer["take_amount"], # Use decimal amount
        to=offer["maker"]
    )
    # transfer offer_token amount to taker
    I.import_module(offer["offer_token"]).transfer(
        amount=offer["offer_amount"], # Use decimal amount
        to=ctx.caller
    )

    # --- Final State Update ---
    offer["status"] = "EXECUTED"
    offer["taker"] = ctx.caller
    otc_listing[listing_id] = offer


@export
def cancel_offer(listing_id: str):
    offer = otc_listing[listing_id]
    assert offer, "Offer ID does not exist" # Check existence first
    assert offer["status"] == "OPEN", "Offer can not be cancelled"
    assert offer["maker"] == ctx.caller, "Only maker can cancel offer"

    # Calculate fee refund amount using decimal
    maker_fee = offer["offer_amount"] / decimal("100.0") * offer["fee"]
    amount_to_refund = offer["offer_amount"] + maker_fee

    # --- CRITICAL CHANGE: Transfer funds back BEFORE updating state ---
    # If this transfer fails, the transaction reverts, and the offer remains OPEN.
    I.import_module(offer["offer_token"]).transfer(
        amount=amount_to_refund, # Use decimal amount
        to=ctx.caller
    )

    # --- Update State (Only if transfer succeeded) ---
    offer["status"] = "CANCELLED"
    otc_listing[listing_id] = offer


@export
def adjust_fee(trading_fee: float): # Use decimal
    # Use precise comparison for owner
    assert ctx.caller == owner.get(), "Only owner can call this method!"
    # Compare with decimal bounds
    assert decimal("0.0") <= trading_fee <= decimal("10.0"), "Fee must be between 0.0 and 10.0 percent"
    fee.set(trading_fee) # Set as decimal


@export
def withdraw(token_list: list):
    # Use precise comparison for owner
    assert ctx.caller == owner.get(), "Only owner can call this method!"

    for token in token_list:
        # Get the amount of earned fees (already Decimal)
        amount_to_withdraw = earned_fees[token]

        # Check if there's anything to withdraw (comparison with Decimal)
        if amount_to_withdraw > decimal("0.0"):
            # 1. Attempt the transfer first.
            # If I.import_module(token).transfer(...) fails (e.g., due to
            # insufficient contract balance, token contract rules, etc.),
            # it should raise an error (like AssertionError in the token contract).
            # This error will halt execution here and cause the entire transaction
            # to revert. earned_fees[token] will NOT be changed in that case.
            I.import_module(token).transfer(
                amount=amount_to_withdraw, # Use Decimal amount
                to=owner.get()
            )

            # 2. Reset the counter *only if* the transfer succeeded.
            # This line is only reached if the I.import_module(token).transfer(...)
            # call above completed without raising an error.
            earned_fees[token] = decimal("0.0")

# Read-only functions remain largely the same, ensure they handle decimal correctly if needed
@export
def view_earned_fees(token: str):
    # earned_fees already stores decimal, including default
    return earned_fees[token]

@export
def view_contract_balance(token: str):
    # Assuming ForeignHash returns compatible types (like decimal or float)
    # If it returns float, consider casting to decimal if needed downstream
    balances = ForeignHash(foreign_contract=token, foreign_name='balances')
    token_balance = balances[ctx.this]
    # Ensure returning decimal for consistency
    return decimal(str(token_balance)) if token_balance is not None else decimal("0.0")