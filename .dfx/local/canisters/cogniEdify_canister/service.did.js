export const idlFactory = ({ IDL }) => {
  const LeaderboardEntry = IDL.Record({
    'username' : IDL.Text,
    'points' : IDL.Nat,
  });
  const Topic = IDL.Record({
    'id' : IDL.Nat32,
    'title' : IDL.Text,
    'progress' : IDL.Nat,
    'shared_with' : IDL.Vec(IDL.Text),
    'objectives' : IDL.Text,
  });
  const User = IDL.Record({
    'id' : IDL.Nat32,
    'username' : IDL.Text,
    'badges' : IDL.Vec(IDL.Text),
    'email' : IDL.Text,
    'points' : IDL.Nat,
  });
  return IDL.Service({
    'createTopic' : IDL.Func([IDL.Nat32, IDL.Text, IDL.Text], [IDL.Text], []),
    'createUser' : IDL.Func([IDL.Nat32, IDL.Text, IDL.Text], [IDL.Text], []),
    'getLeaderboard' : IDL.Func([], [IDL.Vec(LeaderboardEntry)], []),
    'getTopic' : IDL.Func([IDL.Nat32], [IDL.Opt(Topic)], []),
    'getUser' : IDL.Func([IDL.Nat32], [IDL.Opt(User)], []),
  });
};
export const init = ({ IDL }) => { return []; };
