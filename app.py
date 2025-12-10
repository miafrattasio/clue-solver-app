from flask import Flask, render_template, request, session, redirect, url_for
from clue_solver import ClueDeductionEngine, ORIGINAL_CARDS, MASTER_DETECTIVE_CARDS, HAS_CARD, NO_CARD

import os
import json

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key')



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

#new
def render_card_groups(suspects, weapons, rooms):
    """Generates the HTML for the starting hand checkboxes."""
    html = ''
    # Structure the cards into groups for iteration
    card_sets = [('Suspects', suspects), ('Weapons', weapons), ('Rooms', rooms)]
    for title, cards in card_sets:
        html += f'<div class="card-group"><h4>{title}</h4>'
        for card in cards:
            html += f'<label><input type="checkbox" name="hand_cards" value="{card}">{card}</label>'
        html += '</div>'
    return html

app.jinja_env.globals.update(render_card_groups=render_card_groups)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    engine = get_engine()
    
    # When engine is not yet created we show the setup page
    if engine is None:
        # detect edition from form if submitted, otherwise default to 'original'
        edition = request.form.get('version') if request.method == 'POST' else request.args.get('edition', 'original')
        if edition not in ('original', 'master'):
            edition = 'original'

        # select the correct card sets
        card_sets = ORIGINAL_CARDS if edition == 'original' else MASTER_DETECTIVE_CARDS
        # create flat lists for template convenience
        suspects = card_sets['Suspect']
        weapons = card_sets['Weapon']
        rooms = card_sets['Room']

        # If POST, initialize game
        if request.method == 'POST' and 'version' in request.form:
            try:
                version = request.form.get('version')
                card_sets_for_engine = ORIGINAL_CARDS if version == 'original' else MASTER_DETECTIVE_CARDS

                user_name = request.form.get('user_name').strip()
                other_players_input = request.form.get('other_players')
                other_players = [p.strip() for p in other_players_input.split(',') if p.strip()]
                player_names = [user_name] + other_players

                hand_cards = request.form.getlist('hand_cards') 
                hand_cards = [c.strip() for c in hand_cards if c.strip()]
                # getlist to read multi-select starting hand
                hand_cards = request.form.getlist('hand_cards')
                hand_cards = [c.strip() for c in hand_cards if c.strip()]

                engine = ClueDeductionEngine(player_names, card_sets_for_engine, user_name)
                engine.input_player_hand(hand_cards)

                save_engine(engine)
                return redirect(url_for('index'))
            except Exception as e:

                return render_template('setup.html', edition=edition, suspects=suspects, weapons=weapons, rooms=rooms)

        # Render setup template with lists for dropdowns
        return render_template('setup.html', edition=edition, suspects=suspects, weapons=weapons, rooms=rooms)

    else:
        # Handle Opponent's Suggestion Log (Multiple Refuters Logic) 
        if request.method == 'POST' and 'suggester' in request.form:
            try:
                suggester = request.form['suggester'].lower()
                suspect = request.form['suspect']
                weapon = request.form['weapon']
                room = request.form['room']
                suggestion = [suspect, weapon, room]
                refuters = request.form.getlist('refuters') 
                
                engine.log.append(f"Turn Log: {suggester.capitalize()} suggested {suspect}, {weapon}, {room}")
                
                # A. Handle Refuters (Players who showed a card)
                if refuters:
                    for refuter_name in refuters:
                        engine.log_suggestion(suggester, suspect, weapon, room, refuter_name, True)
                        
                    # B. Handle Passers 
                    all_non_refuters = [p for p in engine.players if p != suggester and p not in refuters]
                    
                    for passer in all_non_refuters:
                         for card in suggestion:
                             engine._update_knowledge(card, passer.lower(), NO_CARD)
                             
                else:
                    engine.log.append("No one showed a card. All other players must not have any of these cards.")
                    
                    for player in engine.players:
                        if player != suggester:
                            for card in suggestion:
                                engine._update_knowledge(card, player.lower(), NO_CARD)


                save_engine(engine)
                return redirect(url_for('index'))
            except Exception as e:
                engine.log.append(f"ERROR: Application logic failed on turn log. Details: {e}")
                save_engine(engine)
                return redirect(url_for('index'))


        # Get data for rendering
        solution, header, table, possibilities, cards_shown_history = engine.get_status_summary()
        current_log = engine.log
        engine.log = [] 
        save_engine(engine)

        # Build a mapping from card name -> table row for deterministic lookups in template
        table_map = { row[0]: row for row in table }

        # Render the main game template
        return render_template(
            'game.html',
            players=[p.capitalize() for p in engine.players], 
            user_name=engine.user_name,
            card_sets=engine.card_sets,
            solution=solution,
            header=header,
            table=table,
            table_map=table_map,               
            possibilities=possibilities,
            log=current_log,
            cards_shown_history=cards_shown_history 
        )


# Log Refute By User 
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
            
            # Record the card shown in the history tracker
            if suggester in engine.cards_shown_to_player:
                if card_shown not in engine.cards_shown_to_player[suggester]:
                    engine.cards_shown_to_player[suggester].append(card_shown)
            
            engine.log.append(f"Turn Log: {suggester.capitalize()} suggested, and you showed{card_shown}.")
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
