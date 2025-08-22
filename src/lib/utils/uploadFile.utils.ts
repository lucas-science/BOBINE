const CHROMELEON = 'chromeleon';
const ONLINE = 'online';
const OFFLINE = 'offline';

const PIGNA =  'pigna';
const CONTEXT = 'context';



export const FILE_ZONE = {
  pigna: [{ zone: PIGNA,    max_files: 5 }],
  chromeleon: [
    { zone: ONLINE,  max_files: 5 },
    { zone: OFFLINE, max_files: 1 },
  ],
} as const;