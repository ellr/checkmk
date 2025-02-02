// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef Comment_h
#define Comment_h

#include "config.h"  // IWYU pragma: keep

#include <chrono>
#include <string>

#include "livestatus/Interface.h"
#include "nagios.h"

class Comment {
public:
    unsigned long _id;
    std::string _author;
    std::string _comment;
    CommentType _entry_type;
    std::chrono::system_clock::time_point _entry_time;
    // --------------------------------------------------
    bool _is_service;
    host *_host;
    service *_service;
    std::chrono::system_clock::time_point _expire_time;
    bool _persistent;
    CommentSource _source;
    bool _expires;
};

#endif  // Comment_h
