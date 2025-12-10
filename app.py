# Imports remain the same
from flask import Flask, render_template, request, session, redirect, url_for
from clue_solver import ClueDeductionEngine, ORIGINAL_CARDS, MASTER_DETECTIVE_CARDS, HAS_CARD, NO_CARD

import os
import json

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')


# Custom Encoder/Decoder remain the same
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ClueDeductionEngine):
            return obj.to_json()
        return json.JSONEncoder.default(self, obj)

class CustomDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if 'knowledge' in obj and 'players' in obj:
            return ClueDeductionEngine.from_json(obj)
        return obj

def get_engine():
    if 'engine_json' in session:
        engine_data = json.loads(session['engine_json'], cls=CustomDecoder)
        return engine_data
    return None

def save_engine(engine):
    session['engine_json'] = json.dumps(engine, cls=CustomEncoder)


@app.route('/', methods=['GET', 'POST'])
def index():
    engine = get_engine()
    
    if request.method == 'POST':
        if 'version' in request.form and engine is None:
            # Setup logic remains the same
            version = request.form.get('version')
            card_sets = ORIGINAL_CARDS if version == 'original' else MASTER_DETECTIVE_CARDS
            
            user_name = request.form.get('user_name').strip()
            other_players_input = request.form.get('other_players')
            other_players = [p.strip() for p in other_players_input.split(',') if p.strip()]
            
            player_names = [user_name] + other_players
            hand_cards = [c.strip() for c in request.form.get('hand_cards').split(',') if c.strip()]
            
            engine = ClueDeductionEngine(player_names, card_sets, user_name)
            engine.input_player_hand(hand_cards)
            
            save_engine(engine)
            return redirect(url_for('index'))

    if engine is None:
        return render_template('setup.html')
    else:
        # --- Handle Opponent's Suggestion Log (Multiple Refuters Logic) ---
        if request.method == 'POST' and 'suggester' in request.form:
            try:
                suggester = request.form['suggester'].lower()
                suspect = request.form['suspect']
                weapon = request.form['weapon']
                room = request.form['room']
                suggestion = [suspect, weapon, room]
                refuters = request.form.getlist('refuters') 
                
                engine.log.append(f"--- Turn Log: **{suggester.capitalize()}** suggested **{suspect}**, **{weapon}**, **{room}** ---")
                
                # A. Handle Refuters (Players who showed a card)
                if refuters:
                    for refuter_name in refuters:
                        engine.log_suggestion(suggester, suspect, weapon, room, refuter_name, True)
                        
                    # B. Handle Passers (Players who did NOT show a card)
                    all_non_refuters = [p for p in engine.players if p != suggester and p not in refuters]
                    
                    for passer in all_non_refuters:
                         for card in suggestion:
                             engine._update_knowledge(card, passer.lower(), NO_CARD)
                             
                else:
                    # C. Handle No Refuters (Suggestion went all the way around)
                    engine.log.append("-> Elimination: Suggestion went all the way around. EVERY player must be marked NO CARD for these three cards.")
                    for player in engine.players:
                        for card in suggestion:
                            engine._update_knowledge(card, player.lower(), NO_CARD)

                save_engine(engine)
                return redirect(url_for('index'))
            except Exception as e:
                engine.log.append(f"ERROR: Application logic failed on turn log. Details: {e}")
                save_engine(engine)
                return redirect(url_for('index'))


        # Get data for rendering
        # NEW: The get_status_summary now returns the card history
        solution, header, table, possibilities, cards_shown_history = engine.get_status_summary()
        current_log = engine.log
        engine.log = [] 
        save_engine(engine)
        
        # Render the main game template
        return render_template(
            'game.html',
            players=[p.capitalize() for p in engine.players], 
            user_name=engine.user_name,
            card_sets=engine.card_sets,
            solution=solution,
            header=header,
            table=table,
            possibilities=possibilities,
            log=current_log,
            cards_shown_history=cards_shown_history # NEW: Passing history to the template
        )


# --- Log Refute By User (Updated to track card shown) ---
@app.route('/log_refute_by_user', methods=['POST'])
def log_refute_by_user():
    engine = get_engine()
    if engine is None:
        return redirect(url_for('index'))
    
    try:
        card_shown = request.form['card_shown']
        suggester = request.form['suggester'].lower() 
        
        if card_shown in engine.all_cards:
            engine._update_knowledge(card_shown, engine.user_name, HAS_CARD)
            
            # CRITICAL ADDITION: Record the card shown in the history tracker
            if suggester in engine.cards_shown_to_player:
                if card_shown not in engine.cards_shown_to_player[suggester]:
                    engine.cards_shown_to_player[suggester].append(card_shown)
            
            engine.log.append(f"--- Turn Log: **{suggester.capitalize()}** suggested, and **YOU** refuted by showing **{card_shown}**.")
        else:
            engine.log.append(f"ERROR: Could not log your refutation. Card '{card_shown}' not recognized.")
    except Exception as e:
        engine.log.append(f"ERROR: Application logic failed on user refute. Details: {e}")
        
    save_engine(engine)
    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    session.pop('engine_json', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))