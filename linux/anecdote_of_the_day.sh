#!/bin/bash

# Programming Anecdote of the Day
function show_random_anecdote() {
  anecdotes=(
    "A bug in the code turned out to be a typo in the comment."
    "Spent hours debugging, only to realize I was in the wrong directory."
    "Wrote a regex so complex, even I don't understand it anymore."
    "Fixed one bug, created three new ones. Classic."
    "The code worked perfectly—until someone used it."
    "My TODO list has TODOs inside TODOs."
    "I named a variable 'data' and now I have no idea what it holds."
    "Stack Overflow is my co-pilot."
    "I once solved a bug by deleting the code and rewriting it from scratch."
    "The code compiles. That’s suspicious."
    "I commented out a line and everything broke."
    "My code runs faster when I don’t look at it."
    "I added logging and now I know nothing and everything at once."
    "The function name is 'doStuff'. It does too much stuff."
    "I wrote a test that tests nothing but my patience."
    "I fixed the bug by turning the computer off and on again."
    "I used AI to write code. Now I need AI to explain it."
    "My code is DRY—Don’t Repeat Yourself. Except for the bugs."
    "I renamed a file and Git declared war."
    "I once debugged a problem by talking to a rubber duck. It judged me."
    "I used recursion to solve a problem. Now I have a stack overflow."
    "I added a comment: 'Don’t touch this'. I touched it."
    "My code is secure. It’s so secure even I can’t access it."
    "I used a global variable. Now everything is globally broken."
    "I wrote a script to automate my mistakes."
    "I fixed a bug and introduced a feature. Accidentally."
    "I used a framework to simplify things. Now I need a framework to understand the framework."
    "I spent 3 hours fixing a 3-second delay."
    "I used a lambda function. Now I’m lost in abstraction."
    "I wrote a one-liner. It spans 10 lines now."
    "I used a semicolon. It broke everything."
    "I optimized the code. It’s now unreadable and still slow."
    "I added a feature. The users asked me to remove it."
    "I wrote a comment: 'Magic happens here'. It still does."
    "I used a design pattern. Now I need therapy."
    "I wrote a script to clean up my scripts. It deleted everything."
    "I used a try-catch. It tries, it catches, it fails silently."
    "I wrote a function called 'fixBug'. It creates bugs."
    "I used a boolean flag. It’s always false. Like my hopes."
    "I wrote a unit test. It passed. I don’t trust it."
    "I used recursion. Now I’m stuck in an infinite loop of regret."
    "I added a feature toggle. It toggled my sanity."
    "I used a linter. It linted my soul."
    "I wrote a script to deploy. It deployed chaos."
    "I used async. Now everything happens out of order."
    "I wrote a comment: 'This is temporary'. It’s been 3 years."
    "I used a debugger. It debugged my confidence."
    "I wrote a CLI tool. It insults me when I misuse it."
    "I used a switch statement. It switched sides."
    "I wrote a config file. It configures nothing."
    "I used inheritance. Now I’ve inherited bugs."

  )

  count=${#anecdotes[@]}
  index=$((RANDOM % count))
  echo -e "💡 ${anecdotes[$index]}"
}

show_random_anecdote
