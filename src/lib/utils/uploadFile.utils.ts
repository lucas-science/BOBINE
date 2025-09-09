const ONLINE = 'online';
const OFFLINE = 'offline';

const PIGNAT =  'pignat';
const CONTEXT = 'context';
const CHROMELEON_ONLINE_PERMANENT_GAS = 'chromeleon_online_permanent_gas';


export const FILE_ZONE = {
  context: [{ zone: CONTEXT, max_files: 1 }],
  pignat: [{ zone: PIGNAT,    max_files: 1 }],
  chromeleon: [
    { zone: ONLINE,  max_files: 1 },
    { zone: OFFLINE, max_files: 2 },
  ],
  chromeleon_online_permanent_gas: [{ zone: CHROMELEON_ONLINE_PERMANENT_GAS, max_files: 1 }],
} as const;