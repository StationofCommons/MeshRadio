# Project brief: School of Listening, ZKM

MeshRadio is the first iteration of a Station of Commons installation for the School of Listening at ZKM. The full text is in [Proposal_by_Station_of_Commons.pdf](Proposal_by_Station_of_Commons.pdf). This page keeps the points that shape the hardware and the case.

## Idea

- A network of small stations, each one both sender and receiver, relays an audio stream from one to the next over a local peer-to-peer network. The idea comes from Tetsuo Kogawa's narrow-casting.
- Each station adds its own latency, so a voice spreads through the room over time.
- The visitor's way in is the microphone. Voicing is not limited to speech: whistling, clapping or knocking on a table also count.
- The stations diffuse the audio through directional speakers at places to be agreed.

## Rules the design follows

- The station never records anything. It only relays a constant flow of audio.
- The microphone opens only while a visitor holds a manual push button.
- The network needs no Internet connection.
- The installation is documented in an open repository, so others can build it.

## Materials (five stations)

Raspberry Pi 5, Wi-Fi dongle, push button, microphone, audio adapter, circular LED ring and a 3D printed case, five of each. The Pi boards can be bought from the Station of Commons budget. Sound capture and diffusion can come from ZKM's own equipment.

## Size limit given to the curator

In September the stations were described as no larger than 10 cm high, 8 cm wide and 5 cm deep. They can stand on pedestals or hang from the ceiling, and are spread as far apart as the rooms allow. The case in [`../case/`](../case/) is a 110 mm round puck, so it does not meet that limit yet.

## Schedule

| When | Work |
|---|---|
| 15 Oct to 15 Nov 2026 | Software for two modules, hardware tests, latency tests |
| December | 3D housing with the button built in, then the other modules; documentation |
| January 2027 | Installation |

## Open questions

- Which microphones and directional speakers, once the floor plan shows how the other works are sonified.
- Whether ZKM can print the cases in house. The estimate is 10 to 15 hours of printing for all five.
