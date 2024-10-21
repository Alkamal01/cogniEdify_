import Debug "mo:base/Debug";
import Nat "mo:base/Nat";
import Nat32 "mo:base/Nat32";
import Array "mo:base/Array";

actor YourCanister {

  // User structure
  type User = {
    id: Nat32;
    username: Text;
    email: Text;
    points: Nat;
    badges: [Text];
  };

  // Topic structure
  type Topic = {
    id: Nat32;
    title: Text;
    objectives: Text;
    progress: Nat;
    shared_with: [Text];
  };

  // Leaderboard entry
  type LeaderboardEntry = {
    username: Text;
    points: Nat;
  };

  // Stable variable for storing users and topics
  stable var users: [User] = [];
  stable var topics: [Topic] = [];

  // Functions to handle users
  public shared func createUser(id: Nat32, username: Text, email: Text): async Text {
    let newUser = {
      id = id;
      username = username;
      email = email;
      points = 0;
      badges = [];
    };
    users := Array.append<User>(users, [newUser]);
    Debug.print("User created successfully");
    return "User created successfully";
  };

  public shared func getUser(id: Nat32): async ?User {
    return Array.find<User>(users, func (user: User): Bool {
      return user.id == id;
    });
  };

  // Functions to handle topics
  public shared func createTopic(id: Nat32, title: Text, objectives: Text): async Text {
    let newTopic = {
      id = id;
      title = title;
      objectives = objectives;
      progress = 0;
      shared_with = [];
    };
    topics := Array.append<Topic>(topics, [newTopic]);
    return "Topic created successfully";
  };

  public shared func getTopic(id: Nat32): async ?Topic {
    return Array.find<Topic>(topics, func (topic: Topic): Bool {
      return topic.id == id;
    });
  };

  // Leaderboard function
  public shared func getLeaderboard(): async [LeaderboardEntry] {
    return Array.map<User, LeaderboardEntry>(users, func (user: User): LeaderboardEntry {
      return {
        username = user.username;
        points = user.points;
      };
    });
  }
}
