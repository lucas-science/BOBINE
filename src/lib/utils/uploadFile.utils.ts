const CHROMELEON = 'chromeleon';
const ONLINE = 'online';
const OFFLINE = 'offline';

const PIGNA =  'pigna';
const CONTEXT = 'context';



export const FILE_ZONE = {
    [CHROMELEON]: [{zone: ONLINE, max_files: 5}, {zone: OFFLINE, max_files: 1}],
    [PIGNA]: [{zone: PIGNA, max_files: 1}],
    [CONTEXT]: [{zone: CONTEXT, max_files: 1}],
}

