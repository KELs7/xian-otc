export const getTimeDelta = (timePresent: any, timeFuture: any) => {
    // console.log({timePresent, timeFuture})
    // get total seconds between the times
    var delta = Math.abs(timePresent - timeFuture) / 1000;
  
    // calculate (and subtract) whole days
    var days = Math.floor(delta / 86400);
    delta -= days * 86400;
  
    // calculate (and subtract) whole hours
    var hours = Math.floor(delta / 3600) % 24;
    delta -= hours * 3600;
  
    // calculate (and subtract) whole minutes
    var minutes = Math.floor(delta / 60) % 60;
    delta -= minutes * 60;
  
    // what's left is seconds
    var seconds = Math.floor(delta % 60);
  
    return {
      days,
      hours,
      minutes,
      seconds,
    };
  };

export const getTimeTo = (date: any) => {
    if (!date) return "";
    try {
      let delta = getTimeDelta(new Date(), date);
      if (isNaN(delta.days)) return "";
      if (delta.days > 0) return `${delta.days} days ago`;
      if (delta.hours > 0 && delta.days === 0) return `${delta.hours} hours ago`;
      if (delta.minutes > 0 && delta.hours === 0 && delta.days === 0)
        return `${delta.minutes} minutes ago`;
      if (
        delta.seconds > 0 &&
        delta.minutes === 0 &&
        delta.hours === 0 &&
        delta.days === 0
      )
        return `${delta.seconds} seconds ago`;
      return `now`;
    } catch (e) {
      return "";
    }
  };