const ONLINE = 'online';
const OFFLINE = 'offline';

const PIGNAT =  'pignat';
const CONTEXT = 'context';
const CHROMELEON_ONLINE_PERMANENT_GAS = 'chromeleon_online_permanent_gas';


export const FILE_ZONE = {
  context: [{ zone: CONTEXT, max_files: 1 }],
  pignat: [{ zone: PIGNAT, max_files: 1 }],
  gc_online: [{ zone: ONLINE, max_files: 1 },{ zone: CHROMELEON_ONLINE_PERMANENT_GAS, max_files: 1 }],
  gc_offline: [{ zone: OFFLINE, max_files: 2 }],
} as const;