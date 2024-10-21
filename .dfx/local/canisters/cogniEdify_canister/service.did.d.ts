import type { Principal } from '@dfinity/principal';
import type { ActorMethod } from '@dfinity/agent';
import type { IDL } from '@dfinity/candid';

export interface LeaderboardEntry { 'username' : string, 'points' : bigint }
export interface Topic {
  'id' : number,
  'title' : string,
  'progress' : bigint,
  'shared_with' : Array<string>,
  'objectives' : string,
}
export interface User {
  'id' : number,
  'username' : string,
  'badges' : Array<string>,
  'email' : string,
  'points' : bigint,
}
export interface _SERVICE {
  'createTopic' : ActorMethod<[number, string, string], string>,
  'createUser' : ActorMethod<[number, string, string], string>,
  'getLeaderboard' : ActorMethod<[], Array<LeaderboardEntry>>,
  'getTopic' : ActorMethod<[number], [] | [Topic]>,
  'getUser' : ActorMethod<[number], [] | [User]>,
}
export declare const idlFactory: IDL.InterfaceFactory;
export declare const init: (args: { IDL: typeof IDL }) => IDL.Type[];
