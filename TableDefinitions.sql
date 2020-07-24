
CREATE TABLE Person (
        username VARCHAR(32),
        password VARCHAR(64),
        firstName VARCHAR(32),
        lastName VARCHAR(32),
        email VARCHAR(32),
        PRIMARY KEY (username)
);

CREATE TABLE Photo (
        pID INT AUTO_INCREMENT,
        posterUsername VARCHAR(32),
        postingDate DATETIME,
        allFollowers BOOLEAN,
        caption VARCHAR(1000),
        PRIMARY KEY (pID),
        FOREIGN KEY (posterUsername) REFERENCES Person (username)
);

CREATE TABLE FriendGroup (
        groupName VARCHAR(32),
        creatorUsername VARCHAR(32),
        description VARCHAR(1000),
        PRIMARY KEY (groupName, creatorUsername),
        FOREIGN KEY (creatorUsername) REFERENCES Person (username)
);

CREATE TABLE Reaction (
        pID INT,
        reactorUsername VARCHAR(32),
        reactionTime DATETIME,
        comment VARCHAR(1000),
        emoji BLOB(32),
	PRIMARY KEY (username, pID),
        FOREIGN KEY (pID) REFERENCES Photo (pID),
        FOREIGN KEY (reactorUsername) REFERENCES Person (username)
);

CREATE TABLE Tag (
        pID INT,
        taggedUsername VARCHAR(32),
        tagStatus BOOLEAN,
	PRIMARY KEY (pID, username),
        FOREIGN KEY (pID) REFERENCES Photo (pID),
        FOREIGN KEY (taggedUsername) REFERENCES Person (username)
);


CREATE TABLE Share (
        pID INT,
        groupName VARCHAR(32),
        creatorUsername VARCHAR(32),
	PRIMARY KEY (pID, groupName, creatorUsername),
	FOREIGN KEY (groupName, creatorUsername) REFERENCES FriendGroup(groupName, creatorUsername),
        FOREIGN KEY (pID) REFERENCES Photo (pID)
);



CREATE TABLE GroupMember (
        memberUsername VARCHAR(32),
        groupName VARCHAR(32),
	creatorUsername VARCHAR(32),
        PRIMARY KEY (memberUsername, groupName, creatorUsername),
        FOREIGN KEY (memberUsername) REFERENCES Person (username),
        FOREIGN KEY (groupName, creatorUsername) REFERENCES FriendGroup (groupName, creatorUsername)
);

CREATE TABLE Follow (
        followerUsername VARCHAR(32),
        followeeUsername VARCHAR(32),
        followStatus BOOLEAN,
        PRIMARY KEY (followerUsername, followeeUsername),
        FOREIGN KEY (followerUsername) REFERENCES Person (username),
        FOREIGN KEY (followeeUsername) REFERENCES Person (username)
);
