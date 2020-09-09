# Developers, start your engines!

This guide will walk you through the basics of reinforcement learning (RL), how to train an RL model, and define the reward functions with parameters.

With this knowledge, you’ll be ready to train a model and race in the AWS DeepRacer League.

## What is reinforcement learning?

Reinforcement learning (RL) is a type of machine learning, in which an agent explores an environment to learn how to perform desired tasks by taking actions with good outcomes and avoiding actions with bad outcomes.

A reinforcement learning model will learn from its experience and over time will be able to identify which actions lead to the best rewards.

### Other types of machine learning

* Supervised learning
Example-driven training — with labeled data of known outputs for given inputs, a model is trained to predict output for new inputs.

* Unsupervised learning
Inference-based training — with unlabeled data without known outputs, a model is trained to identify related structures or similar patterns within the input data.

## How does AWS DeepRacer learn to drive by itself?

In reinforcement learning, an agent interacts with an environment with an objective to maximize its total reward.

The agent takes an action based on the environment state and the environment returns the reward and the next state. The agent learns from trial and error, initially taking random actions and over time identifying the actions that lead to long-term rewards.

Let's explore these ideas and how they relate to AWS DeepRacer.

### Agent
The agent simulates the AWS DeepRacer vehicle in the simulation for training. More specifically, it embodies the neural network that controls the vehicle, taking inputs and deciding actions.

### Environment
The environment contains a track that defines where the agent can go and what state it can be in. The agent explores the envrionment to collect data to train the underlying neural network.

### State
A state represents a snapshot of the environment the agent is in at a point in time.

For AWS DeepRacer, a state is an image captured by the front-facing camera on the vehicle.

### Action
An action is a move made by the agent in the current state. For AWS DeepRacer, an action corresponds to a move at a particular speed and steering angle.

### Reward
The reward is the score given as feedback to the agent when it takes an action in a given state.

In training the AWS DeepRacer model, the reward is returned by a reward function. In general, you define or supply a reward function to specify what is desirable or undesirable action for the agent to take in a given state.

## How to train a reinforcement learning model.

### Training an RL model
Training is an iterative process. In a simulator the agent explores the environment and builds up experience. The experiences collected are used to update the neural network periodically and the updated models are used to create more experiences.

With AWS DeepRacer, we are training a vehicle to drive itself. It can be tricky to visualize the process of training, so let's take a look at a simplified example.

### A Simplified Environment
In this example, we want the vehicle to go from the starting point to the finish line following the shortest path.

We've simplified the environment to a grid of squares. Each square represents an individual state, and we'll allow the vehicle to move up or down while facing in the direction of the goal.

### Scores
We can assign a score to each square in our grid to decide what behavior to incentivize.

Here we designate the squares at the edge of the track as "stop states" which will tell the vehicle that it has gone off the track and failed.

Since we want to incentivize the vehicle to learn to drive down the center of the track, we provide a high reward for the squares on the center line, and a low reward elsewhere.

### An episode
In reinforcement training, the vehicle will start by exploring the grid until it moves out of bounds or reaches the destination.

As it drives around, the vehicle accumulates rewards from the scores we defined. This process is called an episode.

In this episode, the vehicle accumulates a total reward of 2.2 before reaching a stop state.

### Iteration
Reinforcement learning algorithms are trained by repeated optimization of cumulative rewards.

The model will learn which action (and then subsequent actions) will result in the highest cumulative reward on the way to the goal.

Learning doesn’t just happen on the first go; it takes some iteration. First, the agent needs to explore and see where it can get the highest rewards, before it can exploit that knowledge.

### Exploration
As the agent gains more and more experience, it learns to stay on the central squares to get higher rewards.

If we plot the total reward from each episode, we can see how the model performs and improves over time.

### Exploitation and Convergence
With more experience, the agent gets better and eventually is able to reach the destination reliably.

Depending on the exploration-exploitation strategy, the vehicle may still have a small probability of taking random actions to explore the environment.

## Parameters of reward functions.

### Reward function parameters for AWS DeepRacer
In AWS DeepRacer, the reward function is a Python function which is given certain parameters that describe the current state and returns a numeric reward value.

The parameters passed to the reward function describe various aspects of the state of the vehicle, such as its position and orientation on the track, its observed speed, steering angle and more.

We will explore some of these parameters and how they describe the vehicle as it drives around the track:

* Position on track
* Heading
* Waypoints
* Track width
* Distance from center line
* All wheels on track
* Speed
* Steering angle

1. Position on track
The parameters `x` and `y` describe the position of the vehicle in meters, measured from the lower-left corner of the environment.

2. Heading
The `heading` parameter describes the orientation of the vehicle in degrees, measured counter-clockwise from the X-axis of the coordinate system.

3. Track width
The `track_width` parameter is the width of the track in meters.

4. Waypoints
The `waypoints` parameter is an ordered list of milestones placed along the track center.

Each waypoint in `waypoints` is a pair `[x, y]` of coordinates in meters, measured in the same coordinate system as the car's position.

5. Distance from center line
The `distance_from_center` parameter measures the displacement of the vehicle from the center of the track.

The `is_left_of_center` parameter is a boolean describing whether the vehicle is to the left of the center line of the track.

6. All wheels on track
The `all_wheels_on_track` parameter is a boolean (true / false) which is true if all four wheels of the vehicle are inside the track borders, and false if any wheel is outside the track.

7. Speed
The `speed` parameter measures the observed speed of the vehicle, measured in meters per second.

8. Steering angle
The `steering_angle` parameter measures the steering angle of the vehicle, measured in degrees.

This value is negative if the vehicle is steering right, and positive if the vehicle is steering left.

9. Summary
In total there are 13 parameters you can use in your reward function

| parameter | descriptions |
| ---- | --- |
| x and y : The position of the vehicle on the track |
| heading : Orientation of the vehicle on the track |
| waypoints : List of waypoint coordinates |
| closest_waypoints : Index of the two closest waypoints to the vehicle |
| progress : Percentage of track completed |
| steps : Number of steps completed |
| track_width : Width of the track |
| distance_from_center : Distance from track center line |
| is_left_of_center : Whether the vehicle is to the left of the center line |
| all_wheels_on_track : Is the vehicle completely within the track boundary? |
| speed : Observed speed of the vehicle |
| steering_angle : Steering angle of the front wheels |

## The Reward Function.

### Putting it all together
With all these parameters at your disposal, you can define a reward function to incentivize whatever driving behavior you like.

Let's see a few examples of reward functions and how they use the parameters to determine a reward. The following three reward functions are available as examples in the AWS DeepRacer console so you can try them out and see how they behave, or submit them to the AWS DeepRacer League.

1. Stay On Track
In this example, we give a high reward for when the car stays on the track, and penalize if the car deviates from the track boundaries.

This example uses the `all_wheels_on_track`, `distance_from_center` and `track_width` parameters to determine whether the car is on the track, and give a high reward if so.

Since this function doesn't reward any specific kind of behavior besides staying on the track, an agent trained with this function may take a longer time to converge to any particular behavior.

2. Follow Center Line
In this example we measure how far away the car is from the center of the track, and give a higher reward if the car is close to the center line.

This example uses the `track_width` and `distance_from_center` parameters, and returns a decreasing reward the further the car is from the center of the track.

This example is more specific about what kind of driving behavior to reward, so an agent trained with this function is likely to learn to follow the track very well. However, it is unlikely to learn any other behavior such as accelerating or braking for corners.

3. No incentive
An alternative strategy is to give a constant reward on each step, regardless of how the car is driving.

This example doesn't use any of the input parameters — instead it returns a constant reward of 1.0 on each step.

The agent's only incentive is to successfully finish the track, and it has no incentive to drive faster or follow any particular path. It may behave erratically.

However, since the reward function doesn't constrain the agent's behavior, it may be able to explore unexpected strategies and behaviors that turn out to perform well.

## Congratulations!

It’s time for the rubber to hit the road. Now that you’ve learned how reward functions translate to improved lap times, you’re ready to enter the AWS DeepRacer League.
