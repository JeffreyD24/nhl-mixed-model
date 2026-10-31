# How sharp betting models get ahead of ours

They're built the same way as ours, with more data, more people and faster information. Here's what each piece means.

## 1. Player tracking data

- **What it is:** since about 2021-22, the NHL has had sensors in the puck and in every player's jersey. Arena cameras and antennas record where every player and the puck are, dozens of times a second. The league calls this NHL EDGE.
- **What it measures:** skating speed and distance, shot speed, time in each zone, how fast a team gets the puck out of its own end, and where everyone was when a shot happened.
- **Who gets it:** a slice is public on the NHL EDGE website, mostly season leaderboards. The full feed is licensed to teams, broadcasters and official betting-data companies.
- **Manual tracking:** companies like Sportlogiq log every pass, zone entry and puck battle from video, and most NHL teams buy it.
- **Why it matters for prediction:** our shot model knows where a shot came from, but not what happened right before it. A shot right after a cross-ice pass, or on a 2-on-1 rush, goes in far more often than the same shot from the same spot with the goalie set. Expected-goals models that include passes and pre-shot movement are noticeably sharper than ones built from shot locations alone, like ours.

## 2. Line-by-line matchups

- **How hockey is played:** teams play in units, usually four forward lines, three defense pairs and power-play units, rotating every 40–50 seconds.
- **Matchups:** coaches try to put their best line against the other team's best. The home team gets the last change, so it controls more of these matchups.
- **The data is public:** the NHL publishes shift charts showing who was on the ice every second of every game. Analysts use them to rate each player by what happens while he's on the ice, adjusted for teammates, opponents and zone starts.
- **Projected lines:** sites like DailyFaceoff post expected line combinations from morning skate. A serious model takes tonight's actual lines, rates each unit, and estimates how much ice time each matchup gets.
- **What ours does instead:** our models treat each team as one block, plus a goalie and a simple "regulars missing" adjustment. If a coach breaks up his top line or moves a defenseman up to the power play, we don't see it. The sharp models do.

## 3. Paid injury news, and speed in general

- **Speed is the whole game here:** the edge isn't secret information so much as getting public information a few minutes before the sportsbook adjusts.
- **Goalies:** in hockey the big one is the starting goalie. By tradition the starter is usually first off the ice at morning skate, and beat reporters post it within minutes. Coaches sometimes confirm starters to reporters around midday.
- **How sharp groups get it first:** they pay for fast alert services, run programs that watch hundreds of beat reporters' social media accounts, and have people following team news. They bet within seconds, before the price moves.
- **Lineups:** the same goes for scratches, call-ups and line changes from morning skate.
- **Where we stand:** our tracker checks ESPN every 5 minutes, and ESPN itself lags the reporters. By the time we see "confirmed," the price has often moved.

## 4. Why they can build all this

- **Resources:** syndicates are small teams of quants and programmers with years of data and accounts at many sportsbooks.
- **The market as a starting point:** they often take the market price as their baseline and only bet where their extra information moves the estimate enough.
- **Execution:** they bet at the opening price right when it posts, with automated systems.

You can see it in the data: our backtests made money only against opening prices, and the closing price was more accurate than either model.

## What this means for us

Three parts of this are reachable for free:

- **Player ratings from shift data:** rating each player by what happens while he's on the ice is a mixed model with players as random effects. It's the same math as BLUP, ridge regression on shifts. You already know this machinery, and the shift charts are public.
- **Projected lines:** feeding DailyFaceoff's projected lines into it would get us part of the line-by-line advantage.
- **Faster goalie news:** checking a faster source than ESPN would help, since the backtest showed that knowing the goalie is where the biggest gain was.

The tracking data and paid news feeds are out of reach on a student budget. The player-level model is probably the most promising next model to add alongside the two we have.
