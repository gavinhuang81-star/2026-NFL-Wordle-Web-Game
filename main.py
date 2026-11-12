
from dataclasses import dataclass
from drafter import *
import csv
import random
import builtins


# -------------------------
# Website Release Settings
# -------------------------

set_website_title("NFL Wordle")
set_site_information(
    author="Gavin Huang",
    description="A fun NFL guessing game that tests your knowledge of NFL players.",
    sources="NFL Wiki",
    planning=[
        "https://docs.google.com/document/d/1WLKggvBcYxs9t1NtnHWWkuGYT-8f8L77ovIJg9lSEzg/edit?tab=t.0#heading=h.1xxqmmg350hh",
        "https://docs.google.com/document/d/1UceyvjJcuawI-39dIBKixagTJEXM2ApqOAafSKuADRM/edit?usp=sharing"],
    links=["https://github.com/gavinhuang81-star/2026-NFL-Wordle-Web-Game.git"])
hide_debug_information()
set_website_framed(False)


# -------------------------
# Dataclasses
# -------------------------

@dataclass
class Guess:
    player_name: str
    results: list[str]


@dataclass
class State:
    gamemode: int
    answer_id: str
    guesses: list[Guess]
    game_over: bool
    message: str
    hard_mode: bool
    players: list["Player"]
    developer_mode: bool


@dataclass
class Teamlist:
    current_team: str
    past_team: list[str]


@dataclass
class Player_numbers:
    current_number: int | None
    past_number: list[int]


@dataclass
class Draft:
    year: int
    draft_round: int | None
    pick_number: int | None
    is_drafted: bool
    team: str


@dataclass
class Player:
    player_id: str
    name: str
    teams: Teamlist
    position: str
    jersey_numbers: Player_numbers
    college: str
    draft: Draft | None
    experience: int | None


# -------------------------
# Data Loading
# -------------------------

def optional_int(value: str) -> int | None:
    value = (value or "").strip()

    if value.lower() in ("", "nan", "none", "null"):
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def load_players() -> list[Player]:
    loaded_players = []

    with builtins.open(
        "2026 active player(NFL) - Sheet1.csv",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            draft_year = optional_int(row["draft_year"])

            if draft_year is None:
                draft = None
            else:
                draft = Draft(
                    year=draft_year,
                    draft_round=optional_int(row["draft_round"]),
                    pick_number=optional_int(row["draft_pick"]),
                    is_drafted=True,
                    team=row["draft_team"] or ""
                )

            player = Player(
                player_id=row["gsis_id"],
                name=row["display_name"],
                teams=Teamlist(
                    current_team=row["latest_team"] or "",
                    past_team=[]
                ),
                position=row["position"] or "",
                jersey_numbers=Player_numbers(
                    current_number=optional_int(row["jersey_number"]),
                    past_number=[]
                ),
                college=row["college_name"] or "",
                draft=draft,
                experience=optional_int(row["years_of_experience"])
            )

            if player.player_id and player.name:
                loaded_players.append(player)

    return loaded_players


# -------------------------
# Helper Functions
# -------------------------

def player_label(player: Player) -> str:
    return player.name + " (" + player.position + ")"


def get_draft_year(player: Player) -> int | None:
    if player.draft is None:
        return None

    return player.draft.year


def get_draft_number(player: Player) -> int | None:
    if player.draft is None:
        return None

    return player.draft.pick_number


def max_guesses_for(state: State) -> int:
    if state.hard_mode:
        return 4
    else:
        return 6


# -------------------------
# Search Players
# -------------------------

def search_players(
    players: list[Player],
    search: str,
    position_filter: str
) -> list[str]:

    results = []
    search_parts = search.lower().strip().split()

    for player in players:
        name_parts = player.name.lower().split()

        if not name_parts:
            continue

        # Filter by position
        if (position_filter != "All Positions" and
                player.position.upper() != position_filter.upper()):
            continue

        # Filter by player name
        if not search_parts:
            match = True

        elif len(search_parts) == 1:
            match = name_parts[0].startswith(search_parts[0])

        else:
            match = (
                name_parts[0].startswith(search_parts[0])
                and name_parts[-1].startswith(search_parts[-1])
            )

        if match:
            results.append(player_label(player))

        if len(results) == 10:
            break

    return results


# -------------------------
# Find Players
# -------------------------

def random_player(players: list[Player]) -> Player:
    return random.choice(players)


def find_player_by_id(
    players: list[Player],
    player_id: str
) -> Player | None:

    for player in players:
        if player.player_id == player_id:
            return player

    return None


def find_player(
    players: list[Player],
    label: str
) -> Player | None:

    for player in players:
        if player_label(player).lower() == label.lower():
            return player

    return None


# -------------------------
# Comparison Functions
# -------------------------

def compare_values(answer, guess, category, display_value):

    if answer is None or guess is None:
        return category + "|N/A|" + str(display_value)

    if answer == guess:
        return category + "|✓|" + str(display_value)

    elif answer > guess:
        return category + "|↑|" + str(display_value)

    else:
        return category + "|↓|" + str(display_value)


def compare_exact(answer, guess, category, display_value):

    if answer == guess:
        return category + "|✓|" + str(display_value)

    return category + "|✗|" + str(display_value)


def position_group(position: str) -> str:

    offense = [
        "QB", "RB", "FB", "WR", "TE",
        "C", "G", "T", "OL", "OT",
        "OG", "LT", "LG", "RG", "RT"
    ]

    defense = [
        "DL", "DE", "DT", "NT", "EDGE",
        "LB", "ILB", "OLB", "CB", "DB",
        "S", "FS", "SS"
    ]

    special_teams = ["K", "P", "LS"]

    position = position.upper().strip()

    if position in offense:
        return "Offense"

    elif position in defense:
        return "Defense"

    elif position in special_teams:
        return "Special Teams"

    else:
        return "Unknown"


def compare_position(answer: str, guess: str) -> str:

    answer_group = position_group(answer)
    guess_group = position_group(guess)

    if answer_group == "Unknown" or guess_group == "Unknown":
        status = "GRAY"

    elif answer_group == guess_group:
        status = "GREEN"

    elif (answer_group == "Special Teams"
          or guess_group == "Special Teams"):
        status = "GRAY"

    else:
        status = "YELLOW"

    return "Position|" + status + "|" + guess


# -------------------------
# Game Functions
# -------------------------

def new_game(state: State) -> State:

    if not state.players:
        state.message = "No player data was loaded."
        return state

    answer = random_player(state.players)

    state.answer_id = answer.player_id
    state.guesses = []
    state.game_over = False
    state.message = ""

    return state


def check_guess(
    answer: Player,
    guess: Player,
    hard_mode: bool
) -> list[str]:

    results = []

    # HARD MODE: Three categories
    if hard_mode:

        results.append(
            compare_values(
                get_draft_year(answer),
                get_draft_year(guess),
                "Draft Year",
                get_draft_year(guess)
            )
        )

        results.append(
            compare_values(
                get_draft_number(answer),
                get_draft_number(guess),
                "Draft Number",
                get_draft_number(guess)
            )
        )

        results.append(
            compare_position(answer.position, guess.position)
        )

    # NORMAL MODE: Seven categories
    else:

        results.append(
            compare_position(answer.position, guess.position)
        )

        results.append(
            compare_values(
                answer.jersey_numbers.current_number,
                guess.jersey_numbers.current_number,
                "Number",
                guess.jersey_numbers.current_number
            )
        )

        results.append(
            compare_values(
                get_draft_year(answer),
                get_draft_year(guess),
                "Draft Year",
                get_draft_year(guess)
            )
        )

        results.append(
            compare_exact(
                answer.teams.current_team,
                guess.teams.current_team,
                "Team",
                guess.teams.current_team
            )
        )

        results.append(
            compare_values(
                answer.experience,
                guess.experience,
                "Experience",
                guess.experience
            )
        )

        results.append(
            compare_exact(
                answer.college,
                guess.college,
                "College",
                guess.college
            )
        )

        results.append(
            compare_exact(
                answer.player_id,
                guess.player_id,
                "Name",
                guess.name
            )
        )

    return results


# -------------------------
# Display Functions
# -------------------------

def make_result_box(result: str):

    parts = result.split("|", 2)

    category = parts[0]
    status = parts[1]
    value = parts[2]

    background = "white"
    display_status = status

    if status == "GREEN" or status == "✓":
        background = "lightgreen"
        display_status = "✓"

    elif status == "YELLOW":
        background = "yellow"
        display_status = "?"

    elif status == "GRAY":
        background = "lightgray"
        display_status = "?"

    elif status == "RED" or status == "✗":
        background = "lightcoral"
        display_status = "✗"

    return Div(
        change_text_size(Header(category, 3), "12px"),
        change_text_size(value, "14px"),
        change_text_size(display_status, "12px"),
        style_border="2px solid gray",
        style_border_radius="8px",
        style_padding="10px",
        style_margin="4px",
        style_background_color=background
    )

def display_guess(guess_info: Guess):
    boxes = []
    for result in guess_info.results:
        boxes.append(make_result_box(result))
    return Div(*boxes)


# -------------------------
# Home Page
# -------------------------

@route
def index(state: State) -> Page:

    return Page(state, [
        Div(
            Header("NFL Wordle"),
            "Guess the mystery NFL player!",
            style_text_align="center"
        ),
        Div(
            Button("Normal Mode", "/normal_mode"),
            Button("Hard Mode", "/hard_mode_route"),
            Button("Instructions", "/instructions"),
            style_text_align="center"
        )
    ])


# -------------------------
# Game Page
# -------------------------

@route
def gamemode1(state: State) -> Page:
    if not state.players:
        return Page(state, [
            "No player data was loaded. Check your CSV file.",
            Button("Home", "/")
        ])
    if state.answer_id == "":
        state = new_game(state)
    content = [
        Header("NFL Wordle"),
        "Difficulty: " + ("Hard Mode" if state.hard_mode else "Normal Mode"),
        "Guesses remaining: " + str(max(0, max_guesses_for(state) -
                                        len(state.guesses)))]

    # Only show search inputs while the game is active
    if not state.game_over:
        content.extend(["Search for a player:",
            TextBox("player_search", ""),
                        "Filter by position:",
                        SelectBox("position_filter", [
                            "All Positions", "QB", "RB", "FB", "WR",
                            "TE","OL", "C", "G", "T", "OT","DL", "DE",
                            "DT", "LB", "CB", "DB","S", "FS",
                            "SS", "K", "P", "LS"]),
            Button("Search", "/search")])

    # Developer mode
    if state.developer_mode:
        answer = find_player_by_id(
            state.players,
            state.answer_id)
        if answer is not None:
            content.append("Developer Answer: " + player_label(answer))
    content.append(Header("Guesses"))

    # Display previous guesses
    for guess_info in state.guesses:
        content.append(guess_info.player_name)
        content.append(display_guess(guess_info))
    if state.message:
        content.append(state.message)
    if state.game_over:
        content.append(Button("New Game", "/new_game_route"))
    content.append(Button("Home", "/"))
    return Page(state, content)

# -------------------------
# Search Page
# -------------------------

@route
def search(state: State,player_search: str,position_filter: str) -> Page:
    results = search_players(state.players,
        player_search,
        position_filter)
    content = [Header("Search Results"),
        "Players found:"]
    if results:
        content.append(SelectBox("player_guess", results))
        content.append(Button("Submit Guess", "/guess"))
    else:
        content.append("No players found.")
    content.append(Button("Search Again", "/gamemode1"))
    content.append(Button("Home", "/"))
    return Page(state, content)

# -------------------------
# Guess Page
# -------------------------

@route
def guess(state: State, player_guess: str) -> Page:
    answer = find_player_by_id(state.players,
        state.answer_id)
    guessed_player = find_player(state.players,
        player_guess)
    if state.game_over:
        return gamemode1(state)
    if answer is None or guessed_player is None:
        state.message = "Could not find that player."
        return gamemode1(state)

    # Compare the guessed player with the answer
    results = check_guess(answer,
        guessed_player,
        state.hard_mode)
    
    # Store the guess
    guess_info = Guess(player_name=player_label(guessed_player),
        results=results)
    state.guesses.append(guess_info)

    # Check whether the answer was guessed
    if guessed_player.player_id == answer.player_id:
        state.message = "Correct! You guessed the player!"
        state.game_over = True
    elif len(state.guesses) >= max_guesses_for(state):
        state.message = ("Game over! The correct answer was " + answer.name)
        state.game_over = True
    else:
        state.message = "Incorrect! Try again."
    return gamemode1(state)

# -------------------------
# New Game Route
# -------------------------

@route
def new_game_route(state: State) -> Page:
    if not state.players:
        return index(state)
    state = new_game(state)
    return gamemode1(state)

# -------------------------
# Difficulty Routes
# -------------------------

@route
def normal_mode(state: State) -> Page:
    if not state.players:
        return index(state)
    state.hard_mode = False
    state.gamemode = 1
    state = new_game(state)
    return gamemode1(state)

@route
def hard_mode_route(state: State) -> Page:
    if not state.players:
        return index(state)
    state.hard_mode = True
    state.gamemode = 2
    state = new_game(state)
    return gamemode1(state)


# -------------------------
# Instructions
# -------------------------

@route
def instructions(state: State) -> Page:

    return Page(state, [Div(Header("How to Play"),
            "1. Search for an NFL player.",
            "2. Select a player from the search results.",
            "3. Submit your guess.",
            "4. Compare your guess with the mystery player.",
            Header("Game Modes"),
            "Normal Mode: 6 guesses and 7 categories.",
            "Hard Mode: 4 guesses and 3 categories.",
            Header("Normal Mode Categories"),

            "Position: Shows whether the position matches or belongs to the same group.",
            "Number: Shows whether the jersey number is higher or lower.",
            "Draft Year: Shows whether the draft year is higher or lower.",
            "Team: Shows whether the current team matches.",
            "Experience: Shows whether years of experience are higher or lower.",
            "College: Shows whether the college matches.",
            "Name: Shows whether you guessed the correct player.",

            Header("Hard Mode Categories"),

            "Draft Year: Shows whether the draft year is higher or lower.",
            "Draft Number: Shows whether the overall draft pick is higher or lower.",
            "Position: Shows whether the position matches or belongs to the same group.",

            Div(Button("Play Game", "/gamemode1"),
                Button("Home", "/"),style_text_align="center"),
            style_text_align="center")])

# Start Server

# Set developer_mode to False before publishing.
start_server(State(0,"",[],False,"",False,load_players(),False))
